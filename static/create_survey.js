$(document).ready(function() {
    let questionCount = 1;

    $('#add-question').click(function() {
        questionCount++;
        var questionHtml = `
            <div class="field">
                <div class="control">
                    <input type="text" class="input" id="question_${questionCount}" name="question" required>
                </div>
            </div>
        `;
        $('#questions-container').append(questionHtml);
    });
});