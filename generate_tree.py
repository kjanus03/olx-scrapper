import os

IGNORE_DIRS = {'venv', 'source', '.idea', '__pycache__', '.git', '.claude', '.cache', 'docs'}

def generate_tree(startpath):
    print(os.path.basename(os.path.abspath(startpath)))
    
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        level = root.replace(startpath, '').count(os.sep)
        if level == 0:
            indent = ''
        else:
            indent = '│   ' * (level - 1) + '├── '
            
        if level > 0:
            print(f'{indent}{os.path.basename(root)}/')
            
        subindent = '│   ' * level + '├── '
        
        for i, f in enumerate(sorted(files)):
            if i == len(files) - 1 and not dirs:
                print('│   ' * level + '└── ' + f)
            else:
                print(f'{subindent}{f}')

if __name__ == '__main__':
    generate_tree('.')