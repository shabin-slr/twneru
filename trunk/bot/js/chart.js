/* MIT-LICENSE */
/*
Copyright (c) 2009 Satoshi Ueyama

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

var launched = false;
var now_canvas = null;
var BAR_GRAD;
var BAR_GRAD2;

function launch()
{
	if (launched) return;

	var t = document.getElementById("main-tbl");
	if (t) {
		launched = true;
		drawChart(t);

		var li = document.getElementById("close-instructions");
		if (li)
			setupInstructionsCloser(li);
	}
}

setTimeout(launch, 100);
setTimeout(launch, 400);
setTimeout(launch, 1000);

function setupInstructionsCloser(li)
{
	var ch = li.childNodes;
	var len = ch.length;
	for (var i = 0;i < len;i++) {
		var e = ch[i];
		if (e.href) {
			e.href = "javascript:void(closeInstructionsBox())";
		}
	}
}

function closeInstructionsBox()
{
	var s = document.getElementById("instructions").style;
	s.opacity = 0;
	setTimeout(function(){s.display = 'none'}, 400);
}

function showWarning(t)
{
	var p = document.createElement('p');
	p.id = "compat-warning";
	p.appendChild(document.createTextNode("このブラウザは Canvas をサポートしていません。グラフの一部は描画されていません。"));
	t.parentNode.insertBefore(p, t);
}

function drawChart(t)
{
	cvs = insertCanvas(document.getElementById("dmy-anc"), t);

	if (cvs) {
		var i;
		var cv = cvs[0];
		var g = cv.getContext('2d');
		var len = TIMES.length;
		var labels = [];

		BAR_GRAD = g.createLinearGradient(0, 0, 24, 0);
		BAR_GRAD.addColorStop(0   ,'rgba(  0,   0,   0, 0.4)');
		BAR_GRAD.addColorStop(0.06,'rgba(200, 200, 200, 0.4)');
		BAR_GRAD.addColorStop(0.14,'rgba(100, 100, 100, 0.2)');
		BAR_GRAD.addColorStop(0.9 ,'rgba(  8,   8,   8, 0.4)');
		BAR_GRAD.addColorStop(1   ,'rgba(  0,   0,   0, 0.8)');

		BAR_GRAD2 = g.createLinearGradient(0, 0, 0, 170);
		BAR_GRAD2.addColorStop(0   ,'rgba(255, 255, 255, 0.3)');
		BAR_GRAD2.addColorStop(0.03,'rgba(255, 255, 255, 0.1)');
		BAR_GRAD2.addColorStop(1   ,'rgba(255, 255, 255,    0)');

		for (i = 0;i < len;i++) {
			var l = drawOne(g, TIMES[i], TIMES[i+1], i);
			if (l)
				labels.push(l);
		}

		for (i = 0;i < len;i++) {
			var l2 = drawOne(g, WTIMES[i], WTIMES[i+1], i, 9);
			if (l2)
				labels.push(l2);
		}

		var img = new Image();
		img.onload = function() {
			for (i = 0;i < len;i++) {
				drawRange(g, TIMES[i], WTIMES[i], i, img);
			}
			drawLabels(g, img, labels);
			drawNow(cvs[1], img);
		}
		img.src = DIGITS;
	}
	else
		showWarning(t);
}

var MIN_HOUR = 15;
var MAX_HOUR = 13;
function drawNow(cv, img)
{
	var now = new Date();
	var nt = now.getTime();

	var yst = new Date();
	yst.setTime(nt - 86400000);

	var h = now.getHours(), m = now.getMinutes();
	var d = now.getDate();
	if (h > MAX_HOUR && h < MIN_HOUR)
		return;

	var h24 = h;
	var h24_label = h24;
	if (h24 < MAX_HOUR) {
		d = yst.getDate();
		h24 += 24;
		if (h24_label<12)
			h24_label += 24;
	}

	var collen = DATES.length;
	var cx, cy;
	if (DATES[collen-1] == d) {
		cx = (collen-1)*31 - 9;
	} else if (DATES[collen-2] == d) {
		cx = (collen-2)*31 - 9;
	} else return;

	cy = Math.floor(((h24-15)*60 + m) * PIX_PER_MIN) - 3;

	if (!now_canvas) {
		var s = cv.style;
		var g = cv.getContext('2d');

		s.left = cx+"px";

		now_canvas = cv;
		g.save();
		g.translate(0, 7);
		drawTimeDigits(g, img, h24_label, m);
		g.restore();

		g.lineWidth = 3;
		g.strokeStyle = "#fff";
		g.beginPath();
		g.moveTo(8, 4);
		g.lineTo(38, 4);
		g.stroke();

		g.lineWidth = 1;
		g.strokeStyle = "#f00";
		g.stroke();
		g.stroke();

		g.drawImage(img, 132, 3, 12, 13, 16, 0, 12, 13);
	}

	cv = now_canvas;
	cv.style.top = cy+"px";
}


function drawTimeDigits(g, img, h, m)
{
	var k = Math.floor(h / 10);
	g.drawImage(img, 12*k, 0, 12, 15,  0, 0, 12, 15);

	k = h % 10;
	g.drawImage(img, 12*k, 0, 12, 15,  8, 0, 12, 15);

	g.drawImage(img, 120, 0, 12, 15, 16, 0, 12, 15);

	k = Math.floor(m / 10);
	g.drawImage(img, 12*k, 0, 12, 15, 20, 0, 12, 15);

	k = m % 10;
	g.drawImage(img, 12*k, 0, 12, 15, 28, 0, 12, 15);
}

function drawLabels(g, img, labels)
{
	var R = 45 * Math.PI / 180;
	var len = labels.length;
	var k;
	for (var i = 0;i < len;i++) {
		var l = labels[i];
		g.save();
		g.translate(l.x-5, l.y-12);
		g.rotate(-R);
		drawTimeDigits(g, img, l.hour, l.min);
		g.restore();
	}
}

function drawOne(g, v1, v2, i, ofs)
{
	if (!ofs)
		ofs = -15

	var x1 = i*31 + 14;
	var t1 = Math.floor(v1/100 +ofs) * 60 + (v1%100);
	var y1 = PIX_PER_MIN * t1;

	if (v2 && v1>=0 && v2>=0) {

		var x2 = (i+1)*31 + 14;
		var t2 = Math.floor(v2/100 +ofs) * 60 + (v2%100);
		var y2 = PIX_PER_MIN * t2;

		var vecX = x2 - x1;
		var vecY = y2 - y1;
		var vecLen = Math.sqrt(vecX*vecX + vecY*vecY);
		if (vecLen < 1) return;

		var x1d = x1 + vecX/vecLen*5;
		var y1d = y1 + vecY/vecLen*5;

		var x2d = x1 + vecX/vecLen*(vecLen-5);
		var y2d = y1 + vecY/vecLen*(vecLen-5);

		g.strokeStyle = "rgba(0,0,0,0.2)";
		g.lineWidth = 3;
		g.beginPath();
		g.moveTo(x1d, y1d);
		g.lineTo(x2d, y2d);
		g.stroke();

		g.strokeStyle = "rgba(255,255,255,0.5)";
		g.lineWidth = 1;
		g.beginPath();
		g.moveTo(x1d, y1d);
		g.lineTo(x2d, y2d);
		g.stroke();
	}

	return (v1<0) ? null : {x: Math.floor(x1), y: Math.floor(y1), hour: Math.floor(v1/100), min: (v1%100)};
}

function drawRange(g, v1, v2, i, img)
{
	if (v1>=0 && v2>=0) {
		var t1 = Math.floor(v1/100 -15) * 60 + (v1%100);
		var y1 = PIX_PER_MIN * t1;

		var t2 = Math.floor(v2/100 +9) * 60 + (v2%100);
		var y2 = PIX_PER_MIN * t2;

		if ((y2-10) > y1) {
			var x1 = i*31 + 14 - 11;
/*
			g.lineWidth = 1;

			g.strokeStyle = "rgba(0,0,0,0.2)";
			g.beginPath(); g.moveTo(x1, y1+2); g.lineTo(x1, y2-3);
			g.stroke();

			x1+=27;
			g.beginPath(); g.moveTo(x1, y1+2); g.lineTo(x1, y2-3);
			g.stroke();

			x1-=15;
			g.lineWidth = 25;
			g.strokeStyle = "rgba(0,0,0,0.3)";
			g.beginPath(); g.moveTo(x1, y1+2); g.lineTo(x1, y2-3);
			g.stroke();

			x1+=5;
			g.lineWidth = 11;
			g.strokeStyle = "rgba(0,0,0,0.16)";
			g.beginPath(); g.moveTo(x1, y1+2); g.lineTo(x1, y2-3);
			g.stroke();

			x1-=15;
			g.lineWidth = 1;
			g.strokeStyle = "rgba(255,255,255,0.1)";
			g.beginPath(); g.moveTo(x1, y1+2); g.lineTo(x1, y2-3);
			g.stroke();

			x1++;
			g.beginPath(); g.moveTo(x1, y1+2); g.lineTo(x1, y2-3);
			g.stroke();

			x1+=19;
			g.lineWidth = 1;
			g.strokeStyle = "rgba(0,0,0,0.3)";
			g.beginPath(); g.moveTo(x1, y1+2); g.lineTo(x1, y2-3);
			g.stroke();
*/
			g.save();
			g.translate(x1, y1);
			g.fillStyle = BAR_GRAD;
			g.fillRect(0, 2, 23, (y2-y1)-6);

			g.fillStyle = BAR_GRAD2;
			g.fillRect(1, 3, 11, (y2-y1)-8);

			g.fillStyle = 'rgba(0,0,0,0.3)';
			g.fillRect(0, (y2-y1)-5, 23, 1);

			g.restore();

			x1 += 22;
			v2 += 2400;
			if ((y2-y1) > 30) {
				g.save();
				var hd = (Math.floor(v2/100) - Math.floor(v1/100)) + ((v2%100) - (v1%100))/60.0;
				g.translate(x1-((hd<10) ? 27 : 23), y1-10 + Math.floor((y2-y1)*0.5));
				drawSleepTime(g, img, hd);
				g.restore();
			}
		}
	}
}

function drawSleepTime(g, img, hours)
{
	if (hours < 0) return;

	var k = Math.floor(hours / 10);
	if (k>0) {
		g.drawImage(img, 12*k, 0, 12, 15,  0, 0, 12, 15);
	}
	var k = Math.floor(hours)%10;
	g.drawImage(img, 12*k, 0, 12, 15,  7, 0, 12, 15);

	var k = Math.floor(hours*10)%10;
	g.drawImage(img, 80, 16, 8, 8, 15, 5, 8, 8);
	g.drawImage(img, 8*k, 16, 8, 8, 18, 5, 8, 8);

}


function insertCanvas(container, target)
{
	var cv = document.createElement("canvas");
	if (!cv.getContext) return null;

	container.style.position = "relative";

	container.appendChild(cv);
	var s = cv.style;
	cv.setAttribute('width', TIMES.length * 31);
	cv.setAttribute('height', 527);
	s.position = "absolute";
	s.left = '-1px';
	s.top  = '2px';
	s.zIndex = 1000;

	var cv2 = document.createElement("canvas");
	container.appendChild(cv2);
	s = cv2.style;

	cv2.setAttribute('width', 50);
	cv2.setAttribute('height', 24);
	cv2.setAttribute('class', 'nowind');

	s.position = "absolute";
	s.left = '-1px';
	s.top  = '2px';
	s.zIndex = 1000;

	return [cv, cv2];
}

var DIGITS = 'data:image/png;base64,'+
    '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'+
    'BPoX1fAj6TuXoYoAAAAASUVORK5CYII=';