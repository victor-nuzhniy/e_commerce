function menuBtnFunction() {
    document.getElementById("menuDown").classList.toggle("show");
}

function catalogBtnFunction() {
    document.getElementById("catalogDown").classList.toggle("show")
}

function popupCatalogBtnFunction() {
    document.getElementById("popupCatalogDown").classList.toggle("show")
}

window.onclick = function(event) {
    if (!event.target.matches('.menu-btn') || event.target.matches('#close-menu-icon')) {
        var menuDowns = document.getElementsByClassName("menu-down-content");
        var i;
        for (i = 0; i < menuDowns.length; i++) {
            var openMenuDown = menuDowns[i];
            if (openMenuDown.classList.contains('show')) {
                openMenuDown.classList.remove('show');
            }
        }
    }
    let elem = document.getElementById("shadow");
    if ((event.target.matches('#shadow') && !event.target.matches('.window'))
     || event.target.matches('.close-window') || event.target.matches('.menu-btn-close')) {
        elem.setAttribute('style', 'display: none');
    }
    if (event.target.matches('#registration') || event.target.matches('#sign-in-down-menu')) {
        elem.style.display = 'block';
    }
    if (event.target.matches('#register-down-menu')) {
        elem.style.display = 'block';
        document.getElementById('log').style.display = 'none';
        document.getElementById('reg').style.display = 'block';
    }
    if (event.target.matches('.sign-in')) {
        document.getElementById('reg').style.display = 'none';
        document.getElementById('log').style.display = 'block';
    }
    if (event.target.matches('.register')) {
        document.getElementById('log').style.display = 'none';
        document.getElementById('reg').style.display = 'block';
    }
    if (event.target.matches('#about-product')) {
        document.getElementsByClassName('product-information')[0].style.display = 'flex';
        document.getElementsByClassName('product-features')[0].style.display = 'none';
        document.getElementById('product-reviews').style.display = 'none';
        document.getElementById('prod-photo').style.display = 'none';
    }
    if (event.target.matches('#product-characteristic')) {
        document.getElementsByClassName('product-features')[0].style.display = 'flex';
        document.getElementsByClassName('product-information')[0].style.display = 'none';
        document.getElementById('product-reviews').style.display = 'none';
        document.getElementById('prod-photo').style.display = 'none';
    }
    if (event.target.matches('#product-rev')) {
        document.getElementById('product-reviews').style.display = 'block';
        document.getElementsByClassName('product-information')[0].style.display = 'none';
        document.getElementsByClassName('product-features')[0].style.display = 'none';
        document.getElementById('prod-photo').style.display = 'none';
    }
    if (event.target.matches('#product-image')) {
        document.getElementById('product-reviews').style.display = 'none';
        document.getElementsByClassName('product-information')[0].style.display = 'none';
        document.getElementsByClassName('product-features')[0].style.display = 'none';
        document.getElementById('prod-photo').style.display = 'flex';
    }
    if (event.target.matches('#filter-text')) {
        document.getElementById('filter-menu').style.display = 'flex';
    }
    if (event.target.matches('#filter-close')) {
        document.getElementById('filter-menu').style.display = 'none';
    }

}