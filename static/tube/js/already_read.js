/* notify.html一般コメントの既読処理 */
$(function(){
    $('#read_btn').click(function() {
        $('input[name=already_read]:checked').each(function() {
        var v = $(this).val();

        let form_elem   = "#already_read";
        let data    = new FormData();
        data.set("id", v);

        let url     = $(form_elem).prop("action");
        let method  = "PATCH";

        //フォーム内のデータを確認できる
        for (let v of data.entries() ){ console.log(v); }

        //Ajaxを送信する
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
                console.log("既読処理完了");
                location.reload(false);
            }
            $('#tab_system_radio_1').prop('checked', true);
            $('input[name=already_read]:checked').prop('checked', false);

        }).fail( function(xhr, status, error) {
            console.log(status + ":" + error );
        });

        });
    });
});

/* notify.html一般コメントの削除処理 */
$(function(){
    $('#comment_delete_btn').click(function() {
        $('input[name=already_read]:checked').each(function() {
        var v = $(this).val();

        let form_elem   = "#comment_delete";
        let data    = new FormData();
        data.set("id", v);

        let url     = $(form_elem).prop("action");
        let method  = "DELETE"
        //let method  = $(form_elem).prop("method");

        //フォーム内のデータを確認できる
        for (let v of data.entries() ){ console.log(v); }

        //Ajaxを送信する
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
                console.log("コメント削除処理完了");
                location.reload(false);
            }
            $('#tab_system_radio_1').prop('checked', true);
            $('input[name=already_read]:checked').prop('checked', false);

        }).fail( function(xhr, status, error) {
            console.log(status + ":" + error );
        });

        });
    });
});

/* notify.html 承認制コメントの既読処理 */

$(function(){
    $('#notify_comment_approval_btn').click(function() {
        $('input[name=comment_approval]:checked').each(function() {
        var v = $(this).val();

        let form_elem   = "#already_read0";
        let data    = new FormData();
        data.set("id", v);

        let url     = $(form_elem).prop("action");
        let method  = "PATCH";

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
                console.log("既読処理完了");
                location.reload(false);
            }
            $('input[name=comment_approval]:checked').prop('checked', false);

        }).fail( function(xhr, status, error) {
            console.log(status + ":" + error );
        });

        });
    });
});

/* notify.html 承認制コメントの削除処理 */

$(function(){
    $('#comment_delete_btn0').click(function() {
        $('input[name=comment_approval]:checked').each(function() {
        var v = $(this).val();

        let form_elem   = "#comment_delete0";
        let data    = new FormData();
        data.set("id", v);

        let url     = $(form_elem).prop("action");
        let method  = "DELETE";

        //フォーム内のデータを確認できる
        for (let v of data.entries() ){ console.log(v); }

        //Ajaxを送信する
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
                console.log("コメント削除処理完了");
                location.reload(false);
            }
            $('input[name=comment_approval]:checked').prop('checked', false);

        }).fail( function(xhr, status, error) {
            console.log(status + ":" + error );
        });

        });
    });
});