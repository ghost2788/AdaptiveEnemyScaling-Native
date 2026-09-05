"""Execute the production rule subset used by allocation tests.

This is NOT the Osiris runtime/compiler. It exercises checked-in PROC/QRY/IF
bodies against explicit native-query fixtures; Toolkit compilation and retail
tests remain required for engine typing, scheduling and status semantics.
Unknown native operations fail loudly rather than silently succeeding.
DB-triggered IF rules react to matching positive additions and non-leading
negative removals, following Larian's documented trigger semantics. PROC/QRY
checks and conditions following an engine event are not database triggers.
"""
import ast
from collections import defaultdict
import re


def call(text):
    match = re.fullmatch(r"(\w+)\((.*)\)", text.strip(), re.S)
    if not match:
        raise AssertionError(f"Unsupported call: {text}")
    args = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', match[2]) if match[2].strip() else []
    return match[1], [re.sub(r"^\(\w+\)", "", arg.strip()) for arg in args]


def value(token, env):
    if token.startswith("_"):
        return env[token]
    if token.startswith('"') or re.fullmatch(r"-?\d+(?:\.\d+)?", token):
        return ast.literal_eval(token)
    return token


def bind(tokens, row, env):
    result = dict(env)
    if len(tokens) != len(row):
        raise AssertionError(f"Arity mismatch: {tokens} / {row}")
    for token, item in zip(tokens, row):
        if token == "_":
            continue
        if token.startswith("_") and token not in result:
            result[token] = item
        elif value(token, result) != item:
            return None
    return result


class StoryFixture:
    def __init__(self, paths):
        self.rules = defaultdict(list)
        self.events = defaultdict(list)
        self.facts = defaultdict(list)
        self.native = defaultdict(list)
        self.timers = {}
        self.applied = []
        self.calls = []
        self.mutations = []
        initial = []
        for path in paths:
            source = re.sub(r"//[^\n]*", "", path.read_text(encoding="utf-8"))
            initial.extend(source.split("INITSECTION", 1)[1].split("KBSECTION", 1)[0].split(";"))
            kb = source.split("KBSECTION", 1)[1].split("EXITSECTION", 1)[0]
            for match in re.finditer(r"(?m)^(IF|PROC|QRY)\s+(.+?)(?=^(?:IF|PROC|QRY)\s|\Z)", kb, re.S):
                conditions, actions = re.split(r"\bTHEN\b", match[2], maxsplit=1)
                terms = re.split(r"\s+AND\s+", conditions.strip())
                name, args = call(terms[0])
                rule = (args, terms[1:], [a.strip() for a in actions.split(";") if a.strip()])
                (self.events if match[1] == "IF" else self.rules)[name].append(rule)
        # Seed data without simulating engine startup events.
        for statement in initial:
            statement = statement.strip()
            if statement and not statement.startswith("NOT "):
                name, args = call(statement)
                if name.startswith("DB_"):
                    self.facts[name].append(tuple(value(a, {}) for a in args))

    def rows(self, name):
        return self.facts[name]

    def add(self, name, *args, fire=True):
        if args not in self.facts[name]:
            self.facts[name].append(args)
            self.mutations.append(("add", name, args))
            if fire:
                self.database_changed(name, args, removed=False)

    def database_changed(self, name, args, *, removed):
        for head, rules in list(self.events.items()):
            if not head.startswith("DB_"):
                continue
            for params, terms, actions in rules:
                conditions = [f"{head}({', '.join(params)})", *terms]
                for index, condition in enumerate(conditions):
                    negative = condition.startswith("NOT ")
                    if negative != removed or (removed and index == 0):
                        continue
                    term = condition[4:] if negative else condition
                    if not term.startswith(name + "("):
                        continue
                    _, tokens = call(term)
                    env = bind(tokens, args, {})
                    if env is not None:
                        for result in self.solutions(conditions, env):
                            for action in actions:
                                self.action(action, result)

    def solutions(self, terms, env):
        if not terms:
            yield env
            return
        term = terms[0]
        if term.startswith("NOT "):
            if not list(self.solutions([term[4:]], env)):
                yield from self.solutions(terms[1:], env)
            return
        comparison = re.fullmatch(r"(\S+)\s+(!=|>=|<=|>|<|==)\s+(\S+)", term)
        if comparison:
            left, right = value(comparison[1], env), value(comparison[3], env)
            matched = {"!=": left != right, ">=": left >= right, "<=": left <= right,
                       ">": left > right, "<": left < right, "==": left == right}[comparison[2]]
            if matched:
                yield from self.solutions(terms[1:], env)
            return
        name, args = call(term)
        if name in self.rules:
            inputs = [value(a, env) for a in args]
            for params, conditions, _ in self.rules[name]:
                local = bind(params, inputs, {})
                if local is not None and next(self.solutions(conditions, local), None) is not None:
                    yield from self.solutions(terms[1:], env)
                    break
            return
        if name.startswith("QRY_") and name not in self.native:
            raise AssertionError(f"Missing query fixture: {name}")
        if name in ("IntegerSum", "ConcatenateGUID", "Concatenate"):
            a, b = [value(x, env) for x in args[:2]]
            rows = [(a, b, a + b)]
        elif name.startswith("DB_"):
            rows = list(self.facts[name])
        elif name in self.native:
            rows = list(self.native[name])
        else:
            raise AssertionError(f"Missing native fixture: {name}")
        for row in rows:
            local = bind(args, row, env)
            if local is not None:
                yield from self.solutions(terms[1:], local)

    def invoke(self, rules, args):
        for params, terms, actions in rules:
            env = bind(params, args, {})
            if env is not None:
                for result in self.solutions(terms, env):
                    for action in actions:
                        self.action(action, result)

    def proc(self, name, *args):
        if name not in self.rules:
            raise AssertionError(f"Missing production procedure: {name}")
        self.invoke(self.rules[name], args)

    def event(self, name, *args):
        self.invoke(self.events[name], args)

    def tick(self):
        pending = list(self.timers)
        for timer in pending:
            self.timers.pop(timer, None)
            self.event("TimerFinished", timer)

    def action(self, text, env):
        remove = text.startswith("NOT ")
        name, tokens = call(text[4:] if remove else text)
        args = tuple(value(token, env) for token in tokens)
        if name.startswith("DB_"):
            if remove:
                if args in self.facts[name]:
                    self.facts[name].remove(args)
                    self.mutations.append(("remove", name, args))
                    self.database_changed(name, args, removed=True)
            else:
                self.add(name, *args)
        elif name.startswith("PROC_"):
            self.proc(name, *args)
        elif name == "TimerLaunch":
            self.timers[args[0]] = args[1]
        elif name == "TimerCancel":
            self.timers.pop(args[0], None)
        elif name == "ApplyStatus":
            self.applied.append(args[:2])
        elif name in ("DebugLog", "RealtimeObjectTimerLaunch", "RealtimeObjectTimerCancel"):
            self.calls.append((name, args))
        else:
            raise AssertionError(f"Unsupported action: {name}")
