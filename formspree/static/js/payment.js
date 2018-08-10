function stripeTokenHandler(token) {
    form.submit();
    // alert('Debugging');
}

function createToken(cardData) {
    stripe.createToken(card, cardData).then(function (result) {
        if (result.error) {
            $('#card-errors').textContent = result.error.message;
        } else {
            stripeTokenHandler(result.token);
        }
    })
}

function stripeSourceHandler(source) {
    // Insert the source ID into the form so it gets submitted to the server
    var form = $('#payment-form');
    form.append($('<input type="hidden" name="stripeSource">').val(source.id));

    // Submit the form
    form.submit();
}

function createSource(ownerInfo) {
    stripe.createSource(card, ownerInfo).then(function (result) {
        if (result.error) {
            // Inform the user if there was an error
            // var errorElement = document.getElementById('card-errors');
            // errorElement.textContent = result.error.message;
            console.log(result.error)
        } else {
            // Send the source to your server
            console.log(result);

            stripeSourceHandler(result.source);
        }
    });
}

$(function () {
    $('#payment-form')[0].addEventListener('submit', function (e) {
        var form = $('#payment-form')[0];
        e.preventDefault();
        // var billing_address = {
        //     name: $('input[name=name]').val(),
        //     address_line1: $('input[name=address_line1]').val(),
        //     address_line2: $('input[name=address_line2]').val(),
        //     address_city: $('input[name=city]').val(),
        //     address_state: ($('select[name=country]').val() === 'US' ? $('input[name=state]').val() : ""),
        //     address_country: $('select[name=country]').val()
        // };

        ownerInfo = {
            owner: {
                name: $('input[name=name]').val(),
                address: {
                    line1: $('input[name=address_line1]').val(),
                    line2: $('input[name=address_line2]').val(),
                    city: $('input[name=city]').val(),
                    state: ($('select[name=country]').val() === 'US' ? $('input[name=state]').val() : ""),
                    country: $('select[name=country]').val()
                },
                email: user_email
            }
        };
        // createToken(billing_address);
        createSource(ownerInfo);
    });
});