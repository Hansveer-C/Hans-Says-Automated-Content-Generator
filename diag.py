
import sys

def check_balance(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    depth = 0
    line_no = 1
    for char in content:
        if char == '\n':
            line_no += 1
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth < 0:
                print(f"Overshoot: extra '}}' at line {line_no}")
                return
    
    print(f"Final depth: {depth}")
    if depth > 0:
        print(f"Incomplete: missing {depth} '}}' at end of file")

if __name__ == "__main__":
    check_balance('static/js/app.js')
