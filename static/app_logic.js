$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/rtls');
    console.log(socket);
    //receive details from server
    socket.on('koordinate', function(msg) {
        console.log(msg.koordinate);
        console.log("Received koordinate" + msg.koordinate[0]);
        console.log("Received koordinate" + msg.koordinate[1]);
        console.log("Received koordinate" + msg.koordinate[2]);
        console.log("Received koordinate" + msg.koordinate[3]);
        console.log("Received koordinate" + msg.koordinate[4]);

        var c = document.getElementById("myCanvas");
        var ctx = c.getContext("2d");
        var imgData = ctx.createImageData(640, 480);
        var cordX=msg.koordinate[1]*2
        var cordY=msg.koordinate[2]*2-80
        var certainty=msg.koordinate[0]
        var width=msg.koordinate[3]*2
        var height=msg.koordinate[4]*2
        var i;
        for (i = 0; i < imgData.data.length; i += 4) {
           imgData.data[i+0] = 255;
           imgData.data[i+1] = 255;
           imgData.data[i+2] = 255;
           imgData.data[i+3] = 255;
        }
        if (msg.koordinate[1]==-1 && msg.koordinate[2]==-1){
	  cordX=-1
	  cordY=-1
	}else{
          var j;
          for (i = 0; i < height; i += 1) {
           for (j = cordX-width; j < cordX; j += 1) {
             imgData.data[(cordY+i)*2*4*320+j*4] = 0;
             imgData.data[(cordY+i)*2*4*320+j*4+1] = 0;
             imgData.data[(cordY+i)*2*4*320+j*4+2] = 0;
             imgData.data[(cordY+i)*2*4*320+j*4+3] = 255;
           }
          }
        }

        console.log(c)
        ctx.putImageData(imgData, 0, 0);
        koordinate_string = '<h3>Koordinata X: </h3>'+'<p>' + cordX.toString() + '</p>' +'<h3>Koordinata Y: </h3>'+ '<p>' + cordY.toString() + '</p>'+'<h3>Certainty: </h3>'+ '<p>' + certainty.toString() + '</p>'+'<h3>Width: </h3>'+ '<p>' + width.toString() + '</p>'+'<h3>Height: </h3>'+ '<p>' + height.toString() + '</p>';
        $('#log').html(koordinate_string);

    });
});
