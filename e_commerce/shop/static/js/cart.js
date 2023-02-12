var updateBtn = document.getElementsByClassName('product-basket-button')
var basketFlag
for (let i = 0; i < updateBtn.length; i++){
    updateBtn[i].addEventListener('click', function(){
        var productId = this.dataset.product
        var action = this.dataset.action
        var sold = this.dataset.sold
        basketFlag = true
        if (sold == 'False'){
            document.getElementById('product-in-cart').style.display = 'flex'
            addCookieItem(productId, action)
        }
    })
}

var quantityBtn = document.getElementsByClassName('cart-quantity')

for (let i = 0; i < quantityBtn.length; i++){
    quantityBtn[i].addEventListener('click', function(){
        var productId = this.dataset.product
        var action = this.dataset.action
        basketFlag = false
        if(user === 'AnonymousUser'){
            addCookieItem(productId, action)
        }else{
            updateUserOrder(productId, action)
        }
    })
}

function reload(){
    location.reload()
}

function addCookieItem(productId, action){
    if(action == 'add'){
        if(cart[productId] == undefined){
            cart[productId] = {'quantity': 1}
        }else{
            cart[productId]['quantity'] += 1
        }
    }

    if(action == 'remove'){
        cart[productId]['quantity'] -= 1
        if(cart[productId]['quantity'] <= 0){
            console.log('Item should be deleted')
            delete cart[productId];
        }
    }
    console.log('Cart:', cart)
    document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/"
    if(basketFlag){
        window.setTimeout(reload, 3000)
    }else{
        reload()
    }
}

function updateUserOrder(productId, action){
    console.log('User is logged in, sending data..')

    addCookieItem(productId, action)
    var url = '/ru/update_item/'

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({'productId': productId, 'action': action})
    })

    .then((response) => {
        return response.json()
    })

    .then((data) => {
        console.log('data:', data)
    })
}

var messageDiv = document.getElementById('cart-message')
var messageWarn = document.getElementById('cart-warning')

if(messageDiv) {
    cartJson = JSON.parse(document.getElementById('cartJson').textContent)
    cart = JSON.parse(cartJson)
    document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/"
    if(!messageWarn){
        window.setTimeout(reload, 10000)
        }
}