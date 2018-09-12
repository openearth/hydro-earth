$("#model-type").change(function () {
    updateModelParameters();
});

function updateModelParameters() {
    let modelType = $("#model-type option:selected").text();
    updateModelParametersForType(modelType);
}

function updateModelParametersForType(modelType) {
    fetch('/models/templates/' + modelType).then(function (response) {
        response.text().then(function (text) {
            $('#parameters').text(text)
        });
    });
}

updateModelParameters();
