function(doc) {
    var tenders = require('views/lib/tenders').main;
    tenders(doc).forEach(function(result) {
        emit(result.key, result.value);
    });
}
