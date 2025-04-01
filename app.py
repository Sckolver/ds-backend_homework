import logging
import io
import json

from flask import Flask, request, jsonify, Response
from models.plate_reader import PlateReader, InvalidImage
from image_provider_client import ImageProviderClient, ImageDownloadError

app = Flask(__name__)
plate_reader = PlateReader.load_from_file('./model_weights/plate_reader_model.pth')
image_provider_client = ImageProviderClient(base_url='http://89.169.157.72:8080', timeout=5.0)


@app.route('/')
def hello():
    user = request.args['user']
    return f'<h1 style="color:red;"><center>Hello {user}!</center></h1>'


@app.route('/greeting', methods=['POST'])
def greeting():
    if not request.is_json:
        return {'error': 'Request must be JSON'}, 400
    body = request.get_json()
    if 'user' not in body:
        return {'error': 'field "user" not found'}, 400

    user = body['user']
    return {
        'result': f'Hello {user}',
    }


@app.route('/readPlateNumber', methods=['POST'])
def read_plate_number():
    im = request.get_data()
    im = io.BytesIO(im)

    try:
        res = plate_reader.read_text(im)
    except InvalidImage:
        logging.error('invalid image')
        return {'error': 'invalid image'}, 400

    return {
        'plate_number': res,
    }


@app.route('/externalReadPlateNumber', methods=['GET'])
def external_read_plate_number():
    image_id_str = request.args.get('image_id')
    if not image_id_str:
        return {'error': 'Parameter "image_id" is required'}, 400

    try:
        image_id = int(image_id_str)
    except ValueError:
        return {'error': 'Parameter "image_id" must be an integer'}, 400

    try:
        image_bytes = image_provider_client.get_image(image_id)
    except ImageDownloadError as e:
        logging.error(f"Error downloading image {image_id}: {e}")
        return {'error': f'Error downloading image {image_id}: {str(e)}'}, 504

    try:
        res = plate_reader.read_text(io.BytesIO(image_bytes))
    except InvalidImage:
        logging.error('Invalid image (Unreadable format)')
        return {'error': 'invalid image format'}, 400
    
    return Response(
        json.dumps({'plate_number': res}, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )


@app.route('/externalBatchReadPlateNumbers', methods=['POST'])
def external_batch_read_plate_numbers():
    if not request.is_json:
        return {'error': 'Request must be JSON'}, 400

    body = request.get_json()
    if 'image_ids' not in body:
        return {'error': 'Missing "image_ids" in request body'}, 400

    image_ids = body['image_ids']
    if not isinstance(image_ids, list):
        return {'error': '"image_ids" must be a list'}, 400

    results = []
    for image_id in image_ids:
        if not isinstance(image_id, int):
            results.append({
                'image_id': image_id,
                'error': 'Image ID must be an integer'
            })
            continue

        try:
            image_bytes = image_provider_client.get_image(image_id)
        except ImageDownloadError as e:
            results.append({
                'image_id': image_id,
                'error': str(e)
            })
            continue
        try:
            plate_num = plate_reader.read_text(io.BytesIO(image_bytes))
            results.append({
                'image_id': image_id,
                'plate_number': plate_num
            })
        except InvalidImage:
            results.append({
                'image_id': image_id,
                'error': 'invalid image format'
            })
    
    return Response(
        json.dumps(results, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] [%(asctime)s] %(message)s',
        level=logging.INFO,
    )

    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=8080, debug=True)
