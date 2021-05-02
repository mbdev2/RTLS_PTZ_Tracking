$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/rtls');
    console.log(socket);
    //receive details from server
    socket.on('koordinate', function(msg) {
      console.log(msg);
        console.log("Received number" + msg.number[0]);
        console.log("Received number" + msg.number[1]);

        var c = document.getElementById("myCanvas");
        var ctx = c.getContext("2d");
        var imgData = ctx.createImageData(640, 480);
        var cordX=msg.number[0]
        var cordY=msg.number[1]
        var i;
        for (i = 0; i < imgData.data.length; i += 4) {
            imgData.data[i+0] = 255;
            imgData.data[i+1] = 255;
            imgData.data[i+2] = 255;
            imgData.data[i+3] = 255;
        }
        var j;
        for (i = 0; i < 20; i += 1) {
          for (j = 0; j < 20; j += 1) {
            imgData.data[(cordY*20+i)*20*32*4+cordX*20*4+j*4] = 0;
            imgData.data[(cordY*20+i)*20*32*4+cordX*20*4+j*4+1] = 0;
            imgData.data[(cordY*20+i)*20*32*4+cordX*20*4+j*4+2] = 0;
            imgData.data[(cordY*20+i)*20*32*4+cordX*20*4+j*4+3] = 255;
          }
        }

        console.log(c)
        ctx.putImageData(imgData, 0, 0);
        number_string = '<h3>Koordinata X: </h3>'+'<p>' + msg.number[0].toString() + '</p>'+ '</br>' +'<h3>Koordinata Y: </h3>'+ '<p>' + msg.number[1].toString() + '</p>';
        $('#log').html(number_string);
    });
});
