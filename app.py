from flask import Flask, render_template, request
import itertools
import re

app = Flask(__name__)

# Tokenizer
def tokenize(expr):
    token_pattern = r'(<->|->|[~&|()])|([A-Z])'
    tokens = []
    for match in re.finditer(token_pattern, expr):
        op, var = match.groups()
        tokens.append(op or var)
    return tokens

# Operator precedence
precedence = {'~': 4, '&': 3, '|': 2, '->': 1, '<->': 0}
right_associative = {'~', '->', '<->'}

def infix_to_postfix(expr):
    tokens = tokenize(expr)
    output = []
    stack = []

    for token in tokens:
        if re.fullmatch(r'[A-Z]', token):
            output.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        elif token in precedence:
            while (stack and stack[-1] != '(' and
                   ((token not in right_associative and precedence[token] <= precedence[stack[-1]]) or
                    (token in right_associative and precedence[token] < precedence[stack[-1]]))):
                output.append(stack.pop())
            stack.append(token)
    while stack:
        output.append(stack.pop())
    return output

def evaluate_postfix(postfix, var_values):
    stack = []
    for token in postfix:
        if token in var_values:
            stack.append(var_values[token])
        elif token == '~':
            stack.append(not stack.pop())
        else:
            b = stack.pop()
            a = stack.pop()
            if token == '&':
                stack.append(a and b)
            elif token == '|':
                stack.append(a or b)
            elif token == '->':
                stack.append((not a) or b)
            elif token == '<->':
                stack.append(a == b)
    return stack[0]

def get_variables(expr):
    return sorted(set(re.findall(r'\b[A-Z]\b', expr)))

def generate_truth_table(expr, variables):
    postfix = infix_to_postfix(expr)
    table = []
    for values in itertools.product([False, True], repeat=len(variables)):
        val_dict = dict(zip(variables, values))
        result = evaluate_postfix(postfix, val_dict)
        table.append((values, result))
    return table, postfix

def build_pdnf_pcnf(table, variables):
    pdnf = []
    pcnf = []

    for vals, res in table:
        if res:
            pdnf.append("(" + " & ".join([v if b else f"~{v}" for v, b in zip(variables, vals)]) + ")")
        else:
            pcnf.append("(" + " | ".join([v if not b else f"~{v}" for v, b in zip(variables, vals)]) + ")")

    return " | ".join(pdnf), " & ".join(pcnf)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        expr = request.form["expr"]
        try:
            variables = get_variables(expr)
            table, postfix = generate_truth_table(expr, variables)
            pdnf, pcnf = build_pdnf_pcnf(table, variables)
            return render_template("index.html", expr=expr, variables=variables, table=table,
                                   postfix=" ".join(postfix), pdnf=pdnf, pcnf=pcnf)
        except Exception as e:
            return render_template("index.html", error=str(e))
    return render_template("index.html")
if __name__ == "__main__":
    app.run(debug=True)