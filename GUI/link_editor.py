import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# 配置日志
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

LINK_ID_FILE = 'C:\\Users\\a0508934\\Documents\\Projects\\OfficeAutomation\\links\\link_id.txt'


@app.route('/get_link_id_data', methods=['GET'])
def get_link_id_data():
    try:
        logging.debug('Received request to get link_id data')
        logging.debug(f'Link ID file path: {LINK_ID_FILE}')
        if os.path.exists(LINK_ID_FILE):
            with open(LINK_ID_FILE, 'r', encoding='utf-8') as file:
                data = file.read()
            return jsonify({'data': data})
        else:
            return jsonify({'data': ''})
    except Exception as e:
        logging.error(f"Error in get_link_id_data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/save_link_id_data', methods=['POST'])
def save_link_id_data():
    try:
        data = request.json.get('data')
        if data:
            with open(LINK_ID_FILE, 'w', encoding='utf-8') as file:
                file.write(data)
            return jsonify({'message': 'Data saved successfully'})
        else:
            return jsonify({'error': 'No data provided'}), 400
    except Exception as e:
        logging.error(f"Error in save_link_id_data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)