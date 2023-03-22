from flask import Flask
from flask import request
from flask import render_template
import math
from local import rocket
import json

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("rocket.html")


@app.route("/ajax", methods=["get", "post"])
def data():
    time = request.values.get("time")
    N = request.values.get("N")
    M = request.values.get("M")
    r = rocket(0j, 500 + 10000j, int(M))
    r.move(int(time), int(N))
    if (int(N) <= 25000):
        # 减少数组的长度以减轻客户端压力及与服务器间传输数据的压力
        pointSample = int(time)
        # 向上取整
        # s = -(-int(N) // pointSample)
        s = math.floor(int(N) / pointSample)
        # jsonnify是flask自带的函数，区别在使用jsonify时响应的Content-Type字段值为application/json
        # 而使用json.dumps时该字段值为text/html，且json.dumps比jsonify可以多接受list类型和一些其他类型的参数
        if (s >= 1):
            return json.dumps((r.orbitSpeed[::s], r.orbitAcceleration[::s],
                               [r.orbit[0][::s], r.orbit[1][::s]],r.orbitAng[::s]))
    else:
        return json.dumps((r.orbitSpeed, r.orbitAcceleration, r.orbit,r.orbitAng))


@app.route("/markdown")
def markdown():
    return render_template("markdown.html")

if __name__ == '__main__':
    # 服务器部署
    # app.run(host="0.0.0.0")
    app.run()

