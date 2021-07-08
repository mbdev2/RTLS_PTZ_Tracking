$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/rtls');
    console.log(socket);
    //receive details from server
    socket.on('koordinate', function(msg) {
        console.log(msg.koordinate);

        var c = document.getElementById("myCanvas");
        var ctx = c.getContext("2d");
        var imgData = ctx.createImageData(640, 480);
        var cordX=msg.koordinate[1]
        var cordY=msg.koordinate[2]
        var certainty=msg.koordinate[0]
        var width=msg.koordinate[3]
        var height=msg.koordinate[4]
        var robYspredaj=msg.koordinate[5]
        var robXlevo=msg.koordinate[6]
        var robXdesno=msg.koordinate[7]
        var robKatederX=msg.koordinate[8]
        var robKatederY=msg.koordinate[9]
        var xSredina=msg.koordinate[10]
        var mejaTable=msg.koordinate[11]
        var mejaKatederY=msg.koordinate[12]
        var mejaKatederXdesno=msg.koordinate[13]
        var mejaKatederXlevo=msg.koordinate[14]


        var i;
        for (i = 0; i < imgData.data.length; i += 4) {
           imgData.data[i+0] = 0;
           imgData.data[i+1] = 0;
           imgData.data[i+2] = 0;
           imgData.data[i+3] = 255;
        }
        if (msg.koordinate[1]==-1 && msg.koordinate[2]==-1){
          cordX=-1
          cordY=-1
        }else{
          //kateder
          var j;
          for (i = robYspredaj; i < 479; i += 1) {
           for (j = robXlevo; j < robXdesno; j += 1) {
             imgData.data[(i)*2*4*320+j*4] = 148;
             imgData.data[(i)*2*4*320+j*4+1] = 169;
             imgData.data[(i)*2*4*320+j*4+2] = 138;
             imgData.data[(i)*2*4*320+j*4+3] = 255;
           }
          }
          //kateder
          var j;
          for (i = robYspredaj; i < mejaKatederY; i += 1) {
           for (j = mejaKatederXlevo; j < mejaKatederXdesno; j += 1) {
             imgData.data[(i)*2*4*320+j*4] = 234;
             imgData.data[(i)*2*4*320+j*4+1] = 179;
             imgData.data[(i)*2*4*320+j*4+2] = 138;
             imgData.data[(i)*2*4*320+j*4+3] = 255;
           }
          }
          //leva talbla
          var j;
          for (i = mejaTable; i < 479; i += 1) {
           for (j = xSredina; j < robXdesno; j += 1) {
             imgData.data[(i)*2*4*320+j*4] = 249;
             imgData.data[(i)*2*4*320+j*4+1] = 218;
             imgData.data[(i)*2*4*320+j*4+2] = 120;
             imgData.data[(i)*2*4*320+j*4+3] = 255;
           }
          }
          //desna tabla
          var j;
          for (i = mejaTable; i < 479; i += 1) {
           for (j = robXlevo; j < xSredina; j += 1) {
             imgData.data[(i)*2*4*320+j*4] = 177;
             imgData.data[(i)*2*4*320+j*4+1] = 208;
             imgData.data[(i)*2*4*320+j*4+2] = 149;
             imgData.data[(i)*2*4*320+j*4+3] = 255;
           }
          }
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

        ctx.putImageData(imgData, 0, 0);
        koordinate_string = '<h3>Koordinata X: </h3>'+'<p>' + cordX.toString() + '</p>' +'<h3>Koordinata Y: </h3>'+ '<p>' + cordY.toString() + '</p>';
        $('#log').html(koordinate_string);

    });
});
