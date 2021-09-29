// reloadを禁止する方法
// F5キーによるreloadを禁止する方法
document.addEventListener("keydown", function (e) {

    if (e.key === 'r' && e.ctrlKey) {
       e.preventDefault();
    }

    if (e.code == 'F5' ) {
       e.preventDefault();
    }
    /*
    if ((e.which || e.keyCode) == 116 ) {
        e.preventDefault();
    }
    */
});