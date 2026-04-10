import os
import glob

def fix_templates():
    for f in glob.glob('backend/**/*.html', recursive=True):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            changes = 0
            if "url_for('app2.login')" in content:
                content = content.replace("url_for('app2.login')", "'http://localhost:5173/sign-in'")
                changes += 1
            if "url_for('app2.signup')" in content:
                content = content.replace("url_for('app2.signup')", "'http://localhost:5173/sign-up'")
                changes += 1
            if "url_for('app2.logout')" in content:
                content = content.replace("url_for('app2.logout')", "'http://localhost:5173/'")
                changes += 1
                
            if changes > 0:
                with open(f, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Fixed {f}")
        except Exception as e:
            print(f"Error processing {f}: {e}")

if __name__ == '__main__':
    fix_templates()
