// 初始化坐标轴
var myChartSpeed = echarts.init(document.getElementById("axies1"), "dark");
var myChartAcceleration = echarts.init(document.getElementById("axies2"), "dark");
var myChartPosition = echarts.init(document.getElementById("axies3"), "dark");
// 刷新网页时初始设定：
// 1、火箭飞行时间setTime
// 3、deltaT=50即50毫秒刷新1次,一秒20帧动画。 
// 4、setTimeControl即控制时间速率(与显示时间相比较)
// 5、为了防止画图数据点过多导致的客户端卡顿，对数组进行如下操作：相隔一点取数据，直到数组只剩setPointSample个数据
// （这可以减少服务器压力，如果数据点不大5则会在服务器上执行）
var setTime = 3000;
var deltaT = 50;
var setTimeControl = 200;
var setPointSample = 3000;
// 记录坐标轴刷新SetInterval的id
var speedId;
var accelerationId;
var positionId;

var style = document.styleSheets[0];


// 网页刷新初始化

// loading
chartShowLoading(myChartSpeed);
chartShowLoading(myChartAcceleration);
chartShowLoading(myChartPosition);

$.ajax({
  url: "/ajax",
  type: "post",
  // 由后端发送的是字段值为text/html的JSON格式的数据(同时有gzip压缩)
  dataType: "json",
  data: { "time": 3000, "N": 10000, "M": 1000 },
  // 异步
  async: true,
  //请求成功时执行该函数内容，result即为服务器返回的json对象
  success: function (result) {
    // 如果没有令dataType:“json”
    // 因为python返回的是Json字符串，需要将其转为与之对应的JavaScript对象。
    // let result = $.parseJSON(result);
    let dataSpeedAll = result[0];
    let dataAccelerationAll = result[1];
    let dataPositionAll = result[2];
    let dataAng = result[3];
    // 取消显示loading
    myChartSpeed.hideLoading();
    myChartAcceleration.hideLoading();
    myChartPosition.hideLoading();
    // 生成echarts图和生成火箭转向动画
    speedId = fnSpeed(dataAng, dataSpeedAll, myChartSpeed, time = setTime, pointSample = setPointSample, timeControl = setTimeControl, dt = deltaT);
    accelerationId = fnAcceleration(dataAccelerationAll, myChartAcceleration, time = setTime, pointSample = setPointSample, timeControl = setTimeControl, dt = deltaT);
    positionId = fnPosition(dataPositionAll, myChartPosition, time = setTime, pointSample = setPointSample, timeControl = setTimeControl, dt = deltaT);
    // style.insertRule("@keyframes animate { 0%, 100% { transform: translateY(-52px) translateX(-50%)}  50% { transform: translateY(-48px) translateX(-50%);}}", 13);
  },
  //请求失败时执行该函数
  error: function () {
    alert("发送ajax请求失败")
  }
});


// 点击“计算火箭轨迹”按钮后

$(document).ready(function () {
  $('#calculate').click(function () {
    chartShowLoading(myChartSpeed);
    chartShowLoading(myChartAcceleration);
    chartShowLoading(myChartPosition);

    $.ajax({
      url: "/ajax",
      type: "post",
      dataType: "json",
      // N表示在火箭发射龙格库塔算法中的采样点数，越大表示精度越好，相对稳定
      data: { "time": $("#time").val(), "N": $("#N").val(), "M": $("#M").val() },
      sync: true,
      //请求成功时执行该函数内容，result即为服务器返回的json对象
      success: function (result) {
        // 由客户端获得用户输入数据
        setTime = $("#time").val();
        setTimeControl = $("#speed").val();
        // 经测试,让数组大小与发射时间保持一致较为合理
        setPointSample = setTime;
        // 获取数据
        let dataSpeedRefresh = result[0];
        let dataAccelerationRefresh = result[1];
        let dataPositionRefresh = result[2];
        let dataAng = result[3];
        // 取消显示loading
        myChartSpeed.hideLoading();
        myChartAcceleration.hideLoading();
        myChartPosition.hideLoading();

        // 考虑到如果在其他ajax响应时，其函数中的SetInterval可能未结束
        // 这样会导致会导致同时在一张图上画两个数据，故要停止SetInterval的运行。
        // 重要※
        clearInterval(speedId);
        clearInterval(accelerationId);
        clearInterval(positionId);
        // 画echarts图和生成火箭转向动画
        speedId = fnSpeed(dataAng, dataSpeedRefresh, myChartSpeed, time = setTime, pointSample = setPointSample, timeControl = setTimeControl, dt = deltaT);
        accelerationId = fnAcceleration(dataAccelerationRefresh, myChartAcceleration, time = setTime, pointSample = setPointSample, timeControl = setTimeControl, dt = deltaT);
        positionId = fnPosition(dataPositionRefresh, myChartPosition, time = setTime, pointSample = setPointSample, timeControl = setTimeControl, dt = deltaT);
      },
      //请求失败时执行该函数
      error: function () {
        alert("发送ajax请求失败")
      }
    });
  });
});



function chartShowLoading(chart) {
  // 设置显示loading时的设定
  chart.showLoading({
    text: 'loading',
    color: 'rgba(255, 255, 255, 0.8)',
    textColor: 'rgba(255, 255, 255, 0.8)',
    maskColor: 'rgba(51,51,51,1)',
  });
}


// echarts选项函数
function echartsOption(titleName, inputData, xAxiesName, yAxiesName) {

  let option = {
    textStyle: {
      fontSize: fontSize(0.15),
    },
    title: {
      text: titleName,
      top: '2%',
      left: '50%',
      // 整体（包括 text 和 subtext）的水平对齐。
      textAlign: 'center',
      textStyle: {
        fontSize: fontSize(0.24),
      },
    },
    tooltip: {
      axisPointer: {
        animation: true
      }
    },
    grid: {
      left: '11.2%',
      right: "13.4%",
      bottom: "12%",
      // containLabel：false 比较适用于多个 grid 进行对齐的场景
      // 因为往往多个 grid 对齐的时候，是依据坐标轴来对齐的。
      containLabel: false,
    },

    xAxis: {
      name: xAxiesName,
      type: "value",
      axisLabel: {
        fontSize: fontSize(0.15),
      },
      // 数据最小值和最大值的延伸范围
      // boundaryGap: [0, 0],
      // 分隔线
      splitLine: {
        show: false,
      },
    },
    yAxis: {
      name: yAxiesName,
      axisLabel: {
        fontSize: fontSize(0.15),
      },
      type: "value",
      boundaryGap: [0, "3%"],
      splitLine: {
        show: false,
      },
    },

    series: [
      {
        name: "rocket",
        type: "line",
        smooth: true,
        showSymbol: false,
        // hover 在拐点标志上的提示动画效果
        hoverAnimation: false,
        // 是否裁剪超出坐标系部分的图形，具体裁剪效果根据系列决定：
        clip: true,
        data: inputData,

      },
    ],
  };
  return option;
  // chart.setOption(option);
}


// 1、生成速度图和设置CSS样式表火箭动画
function fnSpeed(dataAng, dataAll, chart, time = 3000, pointSample = 3000, timeControl = 200, dt = 50) {
  // 若数据点不大，在服务器会进行切片处理以保证数据量在pointSamle附近
  pointN = dataAll.length;
  // 令x坐标满足实际time的量纲
  let xtick = _.range(pointN).map(function (data) { return data * time / pointN });
  let dataSpeed = [];
  let dtNew = dt;
  // echarts选项函数
  let option = echartsOption("Rocket's speed", dataSpeed, "时间(t)", "速度(m/s)");
  // 设置坐标轴chart最初设定 
  chart.setOption(option);

  // 如果数据点大于等于25000，即服务器未执行切片，则执行下列操作：两两数据点间均匀去除一部分点，以至保持数组在(设置5000)pointSample个数据点左右。
  // 以防止画图的数据点过多导致卡顿
  if (pointN >= 25000) {
    // 循环操作:两两数据点间去除一点，直到在(设置5000)pointSample个数据点左右
    // for (let i = 0; i < Math.floor(Math.log2((pointN / pointSample))); i++) {
    //   xtick = xtick.filter(function (num) { return xtick.indexOf(num) % 2 == 0; });
    //   dataAll = dataAll.filter(function (num) { return dataAll.indexOf(num) % 2 == 0; });
    // }
    let N = Math.round(pointN / pointSample)
    xtick = xtick.filter(function (num) { return xtick.indexOf(num) % N == 0; });
    dataAll = dataAll.filter(function (num) { return dataAll.indexOf(num) % N == 0; });
    dataAng = dataAng.filter(function (num) { return dataAng.indexOf(num) % N == 0; });
  }

  pointN = dataAll.length;

  // 当数据不够画一帧时，调整刷新率dt,使得每帧能够画1个点
  if (pointN * dt * timeControl / time / 1000 < 1) {
    dtNew = (1000 * time / pointN / timeControl);
  }

  // 每帧画imax个点
  let imax = Math.round(pointN * dtNew * timeControl / time / 1000);

  let id = setInterval(function () {
    // 对于引用类型的变量，==和===只会判断引用的地址是否相同id
    // js中[]==[]与[]===[]都是false，巨坑
    // 而不会判断对象具体里属性以及值是否相同,所以需要转换为字符串然后判断
    // 当数据生成完毕后停止setInterval的执行
    if (JSON.stringify(dataAll) === JSON.stringify([])) clearInterval(id);

    for (let i = 0; i < imax; i++) {
      // 输入N * dt / time / 1000个(取整)数据，为了保证坐标轴刷新的时间轴的变化和现实同步，即坐标轴动画中的1s=现实中的1s
      dataSpeed.push([xtick.shift(), dataAll.shift()]);
    }
    for (let i = 0; i < imax - 1; i++) {
      dataAng.shift()
    }

    chart.setOption({
      series: [{
        data: dataSpeed,
      },
      ],
    });

    // 根据document.styleSheets，可以知道要改的样式是第0个CSSStyleSheet中第13个CSSStyleRUle;
    let ang = 180 / Math.PI * dataAng.shift() + 90;
    // 写入样式
    style.deleteRule(13);
    // // 在样式表 myStyle 的顶部插入一条新规则
    // style.insertRule("@keyframes animate { 0%, 100% { transform: translateY(-52px) translateX(-50%) rotate(" + ang + "deg); }  50% { transform: translateY(-48px) translateX(-50%) rotate(" + ang + "deg);↵}}", 13);
    style.insertRule("@keyframes animate { 0%, 100% { transform: translateY(2px)  rotate(" + ang + "deg); }  50% { transform: translateY(0px) rotate(" + ang + "deg);↵}}", 13);

  }, dtNew);

  return id;
}

// 2、生成加速度图
function fnAcceleration(dataAll, chart, time = 3000, pointSample = 3000, timeControl = 200, dt = 50) {
  pointN = dataAll.length;
  let xtick = _.range(pointN).map(function (data) { return data * time / pointN });
  let dataAcceleration = [];
  let dtNew = dt;
  // echarts选项函数
  let option = echartsOption("Rocket's acceleration", dataAcceleration, "时间(t)", "加速度(m/s^2)");

  // 设置坐标轴chart最初设定
  chart.setOption(option);
  chart.setOption({
    yAxis: {
      max: 100
    }
  });

  if (pointN >= 25000) {
    // for (let i = 0; i < Math.floor(Math.log2((pointN / pointSample))); i++) {
    // xtick = xtick.filter(function (num) { return xtick.indexOf(num) % 2 == 0; });
    // dataAll = dataAll.filter(function (num) { return dataAll.indexOf(num) % 2 == 0; });
    // }
    let N = Math.round(pointN / pointSample)
    xtick = xtick.filter(function (num) { return xtick.indexOf(num) % N == 0; });
    dataAll = dataAll.filter(function (num) { return dataAll.indexOf(num) % N == 0; });
  }

  pointN = dataAll.length;

  // 当数据不够画一帧时，调整刷新率dt,使得每帧能够画1个点
  if (pointN * dt * timeControl / time / 1000 < 1) {
    dtNew = (1000 * time / pointN / timeControl);
  }

  // 每帧画imax个点
  let imax = Math.round(pointN * dtNew * timeControl / time / 1000);

  let id = setInterval(function () {
    if (JSON.stringify(dataAll) === JSON.stringify([])) clearInterval(id);

    for (let i = 0; i < imax; i++) {
      dataAcceleration.push([xtick.shift(), dataAll.shift()]);
    }


    chart.setOption({
      series: [
        {
          data: dataAcceleration,
        },
      ],
    });
  }, dtNew);

  // 考虑到如果在其他ajax响应中函数中的SetInterval可能未结束
  // 返回setInterval的id值，以便之后停止运行，防止同时在一张图上画两种数据点。
  return id;
}



// 3、生成坐标图
function fnPosition(dataAll, chart, time = 3000, pointSample = 3000, timeControl = 200, dt = 50) {
  pointN = dataAll.length;
  let dataPosition = [];
  let option = echartsOption("Rocket's position", dataPosition, "坐标(m)", "坐标(m)");
  let dtNew = dt;

  chart.setOption(option);

  if (pointN >= 25000) {
    // for (let i = 0; i < Math.floor(Math.log2((pointN / pointSample))); i++) {
    // dataAll[0] = dataAll[0].filter(function (num) { return dataAll[0].indexOf(num) % 2 == 0; });
    // dataAll[1] = dataAll[1].filter(function (num) { return dataAll[1].indexOf(num) % 2 == 0; });
    // }
    let N = Math.round(pointN / pointSample)
    dataAll[0] = dataAll[0].filter(function (num) { return dataAll[0].indexOf(num) % N == 0; });
    dataAll[1] = dataAll[1].filter(function (num) { return dataAll[1].indexOf(num) % N == 0; });
  }

  pointN = dataAll[0].length;

  // 当数据不够画一帧时，调整刷新率dt,使得每帧能够画1个点
  if (pointN * dt * timeControl / time / 1000 < 1) {
    dtNew = (1000 * time / pointN / timeControl);
  }


  let imax = Math.round(pointN * dtNew * timeControl / time / 1000);

  let id = setInterval(function () {
    // 注意到坐标图的数据结构与之前两个图不一样，盈余[[],[]]比较
    if (JSON.stringify(dataAll) === JSON.stringify([[], []])) clearInterval(id);


    for (let i = 0; i < imax; i++) {
      dataPosition.push([dataAll[0].shift(), dataAll[1].shift()]);
    }
    // if (dataAll == []) data = data;
    chart.setOption({
      series: [
        {
          data: dataPosition,
        },
      ],
    });
  }, dtNew);

  return id;
}

// 自适应窗口坐标轴与相应文字大小
$(window).resize(function () {
  let chart = [myChartSpeed, myChartAcceleration, myChartPosition];
  for (var i = 0; i < chart.length; i++) {
    chart[i].resize();

    chart[i].setOption({
      title: {
        textStyle: {
          fontSize: fontSize(0.24),
        },
      },
      textStyle: {
        fontSize: fontSize(0.15),
      },
      xAxis: {
        axisLabel: {
          fontSize: fontSize(0.15),
        },
      },
      yAxis: {
        axisLabel: {
          fontSize: fontSize(0.15),
        },
      },
    });
  };
});
