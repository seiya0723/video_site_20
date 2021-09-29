window.addEventListener("load" , function (){

    $("#comment_refuse").on("click",function(){ comment_refuse(); });
    $("#comment_approval").on("click",function(){ comment_approval(); });

});


function comment_refuse(){

    let form_elem   = ".video_comment_refuse_form";

    let data    = new FormData( $(form_elem).get(0) );
    let url     = $(form_elem).prop("action");
    let method  = $(form_elem).prop("method");

    for (let v of data.entries() ){ console.log(v); }

    $.ajax({
        url: url,
        type: method,
        data: data,
        processData: false,
        contentType: false,
        dataType: 'json'
    }).done( function(data, status, xhr ) {

        if (data.error){
            console.log(data.error);
        }
        else{
            location.reload(false);
        }

    }).fail( function(xhr, status, error) {
        console.log(status + ":" + error );
    });

}


function comment_approval(){

    let form_elem   = ".video_comment_approval_form";

    let data    = new FormData( $(form_elem).get(0) );
    let url     = $(form_elem).prop("action");
    let method  = $(form_elem).prop("method");

    for (let v of data.entries() ){ console.log(v); }

    $.ajax({
        url: url,
        type: method,
        data: data,
        processData: false,
        contentType: false,
        dataType: 'json'
    }).done( function(data, status, xhr ) {

        if (data.error){
            console.log(data.error);
        }
        else{
            location.reload(false);
        }

    }).fail( function(xhr, status, error) {
        console.log(status + ":" + error );
    });

}