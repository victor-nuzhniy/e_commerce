var likeBtn = document.getElementsByClassName('like-button')

if(user != 'AnonymousUser'){
for (let i = 0; i < likeBtn.length; i++){
    likeBtn[i].addEventListener('click', function(){
        addLike(this.dataset.review, this.dataset.author, this.dataset.like)
    })
    }
}

function addLike(review, author, like){
    var url = '/update_like/'

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({'review': review, 'author': author, 'like': like})
    })

    .then((response) => {
        return response.json()
    })

    .then((data) => {
        reload()
    })
}