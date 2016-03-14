jQuery.expr[":"].containsNC = function(elem, i, match) {
    return (elem.textContent || elem.innerText || '').toLowerCase().indexOf((match[3] || '').toLowerCase()) > -1;
};