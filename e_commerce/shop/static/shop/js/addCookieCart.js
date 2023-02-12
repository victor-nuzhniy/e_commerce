cartJson = JSON.parse(document.getElementById('cartJson').textContent)

function reload(){
    location.reload()
}

if(cartJson != "{}"){
    cart = JSON.parse(cartJson)
    document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/"
    window.setTimeout(reload, 1000)
}