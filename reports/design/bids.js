function(doc) {
    var bids = require('views/lib/bids').main;
    (bids(doc) || []).forEach(function(result) {
        emit(result.key, result.value);
    });
}
