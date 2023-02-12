var form = document.querySelector('#filtration')

form.addEventListener('submit', event => {
    event.preventDefault()
    var brand = {}
    var fields = form.elements['brand']
    for(let i = 0; i < fields.length; i++){
        brand[fields[i].value] = fields[i].checked
    }
    var slug = form.elements['slug'].value
    console.log(slug)
    console.log(brand)
})

function updateBrandFilter(brand, slug){
    console.log('Function Filter if active')
    var url = '/category/' + slug + '/'

    fetch(url, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
    },
    body: JSON.stringify(brand)
    })

    .then((response) => {
        return response.json()
    })

    .then((data) => {
        console.log('data:', data)
        reload()
    })
}
