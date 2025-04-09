from flask import Flask, request

app = Flask(__name__)

@app.route('/save', methods=['POST'])
def save_content():
    content = request.form.get('content')
    try:
        with open('测试.txt', 'w', encoding='utf-8') as file:
            file.write(content)
        return '文件保存成功'
    except Exception as e:
        return f'保存文件时出错: {str(e)}'

if __name__ == '__main__':
    app.run(debug=True)
    