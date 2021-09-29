
$(function(){
    $('#mylist_clear_btn').click(function() {
        $('input[name=mylist_chk]:checked').each(function() {
        var v = $(this).val();

        let form_elem   = "#mylist_clear_form";
        let data    = new FormData();
        data.set("id", v);

        let url     = $(form_elem).prop("action");
        let method  = "DELETE";

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
                console.log("マイリスト削除処理完了");
                location.reload(false);
            }
            $('input[name=mylist_chk]:checked').prop('checked', false);

        }).fail( function(xhr, status, error) {
            console.log(status + ":" + error );
        });

        });
    });
});