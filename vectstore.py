from sanic import Sanic
from sanic.response import json
from annoy import AnnoyIndex
from pathlib import Path

app = Sanic()

DATA_PATH = Path('./data/')

@app.route("/")
async def test(request):
    return json({"hello": "world"})

unsaved = {}
loaded = {}

@app.route("/index", methods=['POST'])
async def create_index(request):
    # TODO: Dodać sprawdzenie czy go nie ma
    name = request.json['name']
    dimmensions = request.json['dimmensions']
    metric = request.json.get('metric', 'angular')

    index_obj = AnnoyIndex(dimmensions, metric=metric)
    unsaved[name] = index_obj

    result = {
        'name': name,
        'dimmensions': dimmensions,
        'metric': metric,
        'saved': False
    }
    return json(result)


@app.route('/index/<index_name:[A-z0-9_]+>', methods=['PUT'])
async def save_index(request, index_name):
    n_trees = request.json['n_trees']

    index = unsaved.pop(index_name)
    index.build(n_trees)
    file = (DATA_PATH / index_name).with_suffix('.ann')
    saved = index.save(str(file.absolute()))
    loaded[index_name] = index

    result = {
        'name': index_name,
        'saved': saved,
    }
    return json(result)

@app.route('/index/<index_name:[A-z0-9_]+>', methods=['POST'])
async def add_to_index(request, index_name):

    index = unsaved[index_name]

    id = request.json['id']
    vector = request.json['vector']

    index.add_item(id, vector)

    result = {
        'id': id,
        'added': True,
    }
    return json(result)

@app.route('/index/<index_name:[A-z0-9_]+>', methods=['GET'])
async def query_index(request, index_name):

    index = loaded.get(index_name)

    if index is None:
        dimmensions = 10
        index = AnnoyIndex(dimmensions)
        file = (DATA_PATH / index_name).with_suffix('.ann')
        index.load(str(file.absolute()))
        loaded[index_name] = index

    id = int(request.args['id'][0])
    count = request.args.get('count')
    if count is None:
        count = 10

    items = index.get_nns_by_item(id, count)

    result = {
        'items': items
    }
    return json(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, auto_reload=True, debug=True)
