import numpy as np
import math
import json

class rocket():
    # 不需要修改部分
    def __init__(self, pos, v, M=1000):
        self.x = np.array([pos, v, M])
        self.G = 6.67 * 10**-11
        self.earth = np.array([-1j * 6371 * 10**3, 0j, 6 * 10**24])
        self.R = 6371 * 10**3
        self.m = 900
        self.orbit = [[pos.real], [pos.imag]]
        self.orbitSpeed = [abs(self.x[1])]
        # self.orbitAcceleration = [((self.F(self.x) / self.x[2]).real**2 +(self.F(self.x) / self.x[2]).imag**2)**(0.5)]
        self.orbitAcceleration = [abs(self.F(self.x) / self.x[2])]
        self.orbitAng=[math.pi / 2 - np.angle(self.x[1]) - np.angle(self.x[0] - self.earth[0])]
        self.c = .1

    def func(self, x):  # 微分方程的右侧函数
        if x[2] < self.m:
            return np.array([x[1], self.F(x) / x[2], 0])
        else:
            return np.array([x[1], self.F(x) / x[2], -self.c])

    def move_1(self, dt):  # 龙格库塔法的一步
        K_1 = self.func(self.x)
        K_2 = self.func(self.x + K_1 * (dt / 2))
        K_3 = self.func(self.x + K_2 * (dt / 2))
        K_4 = self.func(self.x + K_3 * dt)
        return self.x + (K_1 + K_2 * 2 + K_3 * 2 + K_4) * dt / 6

    def inearth(self, x):  # 判断是否进入地球内部
        r = x[0] - self.earth[0]
        if abs(r) < self.R - 1:
            return True
        return False

    def outspace(self, x):  # 判断是否飞出地球区域
        r = x[0] - self.earth[0]
        if abs(r) > 2 * self.R:
            return True
        return False

    def rho(self, x):  # 空气密度
        rho0 = 1.225
        T0 = 288.15
        h = abs(x[0] - self.earth[0]) - self.R
        if h <= 11000:
            T = T0 - 0.0065 * h
            return rho0 * (T / T0)**4.25588
        elif h <= 20000:
            T = 216.65
            return 0.36392 * math.exp((-h + 11000) / 6341.62)
        elif h < 32000:
            T = 216.65 + 0.001 * (h - 20000)
            return 0.088035 * (T / 216.65)**-35.1632
        else:
            return 0

    def set_c(self, x):  # 设置火箭的喷射
        anl = math.pi / 2 - np.angle(x[1]) - np.angle(x[0] - self.earth[0])
        if anl < math.pi / 180 * 10 and anl > math.pi / 180 * .1:
            return self.c
        else:
            return 0

    def F(self, x):  # 合外力
        r = x[0] - self.earth[0]
        g = -self.G * self.earth[2] * x[2] * r / abs(r)**3
        T = (8.5 * 10**5) * self.set_c(x) * x[1] / abs(x[1])
        f = -0.08 * .5 * self.rho(x) * x[1] * abs(x[1])
        if abs(r) < self.R and False:
            D = 10**4 * r * (self.R / abs(r) - 1)
        else:
            D = 0
        if x[2] < self.m:
            return g + f + T + D
        return g + f + D

    def move(self, t, N=100):  # 移动一次, 并且画出初始点
        if self.inearth(self.x) or self.outspace(self.x):
            self.x[1] = 0j
        dt = t / N
        for i in range(N):
            self.x = self.move_1(dt)
            self.orbit[0].append(self.x[0].real)
            self.orbit[1].append(self.x[0].imag)
            self.orbitSpeed.append(abs(self.x[1]))
            self.orbitAcceleration.append(abs((self.F(self.x) / self.x[2])))
            self.orbitAng.append(math.pi / 2 - np.angle(self.x[1]) - np.angle(self.x[0] - self.earth[0]))

        return self.orbit

    def jsonOutput(self):
        return json.dumps(r.orbitSpeed)


if __name__=='__main__':
    r = rocket(0j, 500 + 10000j, 1000)
    # for i in range(5):
    #     r.move(300, 2000)
    r.move(3000,10000)
    # file_name="test.json"
    # with open(file_name,'w') as file_obj:
    #     json.dump((r.orbitAng),file_obj)
    # print(json)