$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/rtls');
    console.log(socket);
    //receive details from server
    socket.on('koordinate', function(msg) {
        console.log(msg.frame);

        var c = document.getElementById("myCanvas");
        var ctx = c.getContext("2d");
        var imgData = ctx.createImageData(32, 24);

        var i;
        var vrednostCelice;
        var barva = [0,0,0,255];

        for (i = 0; i < imgData.data.length; i += 4) {
            vrednostCelice=msg.frame[i/4]
            if (vrednostCelice < 19){
                barva = [40,34,87,255];
                }
            else if (vrednostCelice < 21){
                barva = [7,5,243,255];
                }
            else if (vrednostCelice < 23){
                barva = [59,135,118,255];
                }
            else if (vrednostCelice < 25){
                barva = [145,252,77,255];
                }
            else if (vrednostCelice < 27){
                barva = [212,253,81,255];
                }
            else if (vrednostCelice < 29){
                barva = [253,241,80,255];
                }
            else if (vrednostCelice < 31){
                barva = [247,204,70,255];
                }
            else if (vrednostCelice < 33){
                barva = [236,96,47,255];
                }
            else if (vrednostCelice < 35){
                barva = [236,53,36,255];
                }
            else if (vrednostCelice < 37){
                barva = [235,74,94,255];
                }
            else if (vrednostCelice < 39){
                barva = [237,112,173,255];
                }
            imgData.data[i+0] = barva[0];
            imgData.data[i+1] = barva[1];
            imgData.data[i+2] = barva[2];
            imgData.data[i+3] = barva[3];
        }

        console.log(c);
        ctx.putImageData(imgData, 0, 0);
        //number_string = '<h3>Koordinata X: </h3>'+'<p>' + msg.number[0].toString() + '</p>'+ '</br>' +'<h3>Koordinata Y: </h3>'+ '<p>' + msg.number[1].toString() + '</p>';
        //$('#log').html(number_string);
    });
});
