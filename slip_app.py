from flask_app import create_app

app = create_app()


if __name__ == '__main__':
    app.run(host='10.18.130.45')
