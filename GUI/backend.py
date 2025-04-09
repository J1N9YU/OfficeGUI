import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
CORS(app)

# 修改 LINK_ID_FILE 的路径
current_dir = os.path.dirname(os.path.abspath(__file__))
LINK_ID_FILE = os.path.join(current_dir, '../data/link_id.txt')
# 修改 LOGS_DIR 的路径
LOGS_DIR = os.path.join(current_dir, '../data')


@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory(current_dir, 'index.html')


@app.route('/get_link_id_data', methods=['GET'])
def get_link_id_data():
    try:
        logging.debug('Received request to get link_id data')
        logging.debug(f'Link ID file path: {LINK_ID_FILE}')
        if not os.path.exists(LINK_ID_FILE):
            logging.warning('Link ID file does not exist.')
            return jsonify({'data': []})

        tree_data = {}
        with open(LINK_ID_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            current_item = None
            current_customer = None
            current_project = None
            logging.debug('Started reading link_id file.')

            def add_item_to_tree():
                nonlocal current_item, current_customer, current_project
                if current_item and current_customer and current_project:
                    tree_data.setdefault(current_customer, {})
                    tree_data[current_customer].setdefault(current_project, [])
                    tree_data[current_customer][current_project].append(current_item)
                    logging.debug(
                        f'Added item {current_item["title"]} to project {current_project} of customer {current_customer}')
                    current_item = None

            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    add_item_to_tree()
                    title = line[1:].lstrip()  # 去除标题前的空格
                    current_item = {
                        'title': title,
                        'link': None,
                        'emails': [],
                        'log': '',
                        'type': 'default'
                    }
                    logging.debug(f'Found new item: {current_item["title"]}')
                elif line.startswith('customer='):
                    current_customer = line.split('=')[1]
                    logging.debug(f'Found new customer: {current_customer}')
                elif line.startswith('project='):
                    current_project = line.split('=')[1]
                    logging.debug(f'Found new project: {current_project} for customer {current_customer}')
                elif line.startswith('link='):
                    if current_item:
                        current_item['link'] = line.split('=')[1]
                        logging.debug(f'Assigning link {current_item["link"]} to item {current_item["title"]}')
                elif line.startswith('type='):
                    if current_item:
                        current_item['type'] = line.split('=')[1]
                        logging.debug(f'Assigning type {current_item["type"]} to item {current_item["title"]}')
                elif line.startswith('[') and line.endswith(']'):
                    if current_item:
                        current_item['emails'].append(line)
                        logging.debug(f'Added email {line} to item {current_item["title"]}')
                elif not line:
                    add_item_to_tree()

            # 处理最后一个条目
            add_item_to_tree()

            logging.debug('Finished reading link_id file.')
            # 输出已读取的 tree_data 用于调试
            logging.debug(f"Read tree_data: {tree_data}")

            # 检查事项是否有日志文件，没有则生成
            for customer in tree_data:
                for project in tree_data[customer]:
                    for item in tree_data[customer][project]:
                        title = item['title'].lstrip(' _')
                        valid_title = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in title)
                        log_file_name = f'{valid_title}_log.txt'
                        log_file_path = os.path.join(LOGS_DIR, log_file_name)
                        if not os.path.exists(log_file_path):
                            log_header = generate_log_header(customer, project, item)
                            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                                log_file.write(log_header)
                            logging.debug(f'Generated log file for {title} at {log_file_path}')

        return jsonify({'data': tree_data})
    except Exception as e:
        logging.error(f"Error in get_link_id_data: {e}", exc_info=True)
        # 输出已读取的 tree_data 用于调试
        logging.debug(f"Read tree_data before error: {tree_data}")
        return jsonify({'error': str(e), 'partial_data': tree_data}), 500


@app.route('/get_log', methods=['POST'])
def get_log():
    try:
        data = request.json
        title = data.get('title')
        if not title:
            logging.error('Title not provided in request to get log.')
            return jsonify({'error': 'Title not provided'}), 400

        # 去除标题前的空格和下划线
        title = title.lstrip(' _')
        # 确保事项名（title）是有效的文件名
        valid_title = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in title)
        log_file_name = f'{valid_title}_log.txt'
        log_file_path = os.path.join(LOGS_DIR, log_file_name)
        logging.debug(f'Getting log from file: {log_file_path}')
        if not os.path.exists(log_file_path):
            logging.warning(f'Log file {log_file_path} does not exist.')
            return jsonify({'log': ''})

        with open(log_file_path, 'r', encoding='utf-8') as file:
            log_content = file.read()
            logging.debug(f'Successfully read log from {log_file_path}')

        return jsonify({'log': log_content})
    except Exception as e:
        logging.error(f"Error in get_log: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/save_log', methods=['POST'])
def save_log():
    try:
        data = request.json
        title = data.get('title')
        log_content = data.get('log')
        email_titles = data.get('email_titles', [])
        item_type = data.get('type', 'default')
        if not title or not log_content:
            logging.error('Title or log content not provided in request to save log.')
            return jsonify({'error': 'Title or log content not provided'}), 400

        # 去除标题前的空格和下划线
        title = title.lstrip(' _')
        # 确保事项名（title）是有效的文件名
        valid_title = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in title)
        log_file_name = f'{valid_title}_log.txt'
        log_file_path = os.path.join(LOGS_DIR, log_file_name)
        logging.debug(f'Saving log to file: {log_file_path}')

        # 解析现有日志，分离表头和正文
        header = ''
        body = ''
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                header_lines = []
                for i, line in enumerate(lines):
                    if line.strip() == '---':
                        body = ''.join(lines[i + 1:])
                        break
                    header_lines.append(line)
                header = ''.join(header_lines)

        # 更新表头中的邮件标题和类型
        new_header = update_header_with_emails_and_type(header, email_titles, item_type)

        # 写入新的日志内容
        with open(log_file_path, 'w', encoding='utf-8') as file:
            file.write(new_header)
            file.write('---\n')
            file.write(body)
            logging.debug(f'Successfully saved log to {log_file_path}')

        return jsonify({'message': 'Log saved successfully'})
    except Exception as e:
        logging.error(f"Error in save_log: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/add_new_item', methods=['POST'])
def add_new_item():
    try:
        data = request.json
        customer = data.get('customer')
        project = data.get('project')
        item_title = data.get('item_title')
        email_title = data.get('email_title')
        item_type = data.get('type', 'default')

        if not customer or not project or not item_title:
            return jsonify({'error': '客户、项目和事项名称为必填项'}), 400

        # 读取现有文件获取最大 link_id
        max_link_id = 0
        if os.path.exists(LINK_ID_FILE):
            with open(LINK_ID_FILE, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith('link='):
                        try:
                            link_id = int(line.split('=')[1])
                            if link_id > max_link_id:
                                max_link_id = link_id
                        except ValueError:
                            pass

        new_link_id = max_link_id + 1

        # 写入新条目到文件
        with open(LINK_ID_FILE, 'a', encoding='utf-8') as file:
            file.write(f'\n# {item_title}\n')
            file.write(f'customer={customer}\n')
            file.write(f'project={project}\n')
            file.write(f'link={new_link_id}\n')
            file.write(f'type={item_type}\n')
            if email_title:
                file.write(f'[{email_title}]\n')

        # 创建日志文件并添加固定头部
        # 去除标题前的空格和下划线
        item_title = item_title.lstrip(' _')
        valid_title = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in item_title)
        log_file_name = f'{valid_title}_log.txt'
        log_file_path = os.path.join(LOGS_DIR, log_file_name)
        log_header = generate_log_header(customer, project, {
            'title': item_title,
            'link': new_link_id,
            'emails': [f'[{email_title}]'] if email_title else [],
            'type': item_type
        })
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write(log_header)

        return jsonify({'message': '新条目添加成功', 'link_id': new_link_id})
    except Exception as e:
        logging.error(f"Error in add_new_item: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def generate_log_header(customer, project, item):
    title = item['title']
    link = item['link']
    emails = item['emails']
    item_type = item['type']
    header = f'# {customer}_{project}_{title}\n客户: {customer}\n项目: {project}\n类型: {item_type}\n链接: {link}\n'
    for email in emails:
        header += f'{email}\n'
    header += '---\n'
    return header


def update_header_with_emails_and_type(header, email_titles, item_type):
    lines = header.splitlines()
    new_lines = []
    email_started = False
    type_updated = False
    for line in lines:
        if line.startswith('[') and line.endswith(']'):
            if not email_started:
                email_started = True
            continue
        if line.startswith('类型:'):
            new_lines.append(f'类型: {item_type}')
            type_updated = True
            continue
        if line.strip() == '---':
            if not type_updated:
                new_lines.append(f'类型: {item_type}')
            for email_title in email_titles:
                new_lines.append(f'[{email_title}]')
            new_lines.append(line)
            break
        new_lines.append(line)
    return '\n'.join(new_lines)


if __name__ == '__main__':
    app.run(debug=True, port=5500)
  