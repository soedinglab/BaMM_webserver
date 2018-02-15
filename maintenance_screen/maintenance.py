from flask import Flask
app = Flask(__name__)


@app.errorhandler(404)
def maintenance_screen(e):
    message = (
    """
    <div style="width:1000px; margin:0 auto;text-align:center;height:100px;margin-top:30vh">
      <p>
        <h1> Sorry :-(</h1>
        <h1>
          The BaMM web server is shortly under maintenance.
        </h1>
        <h1>
          We will be back as soon as possible.
        </h1>
    </p>
    </div>
    """)

    return message
