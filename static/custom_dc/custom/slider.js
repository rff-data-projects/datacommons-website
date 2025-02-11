//Left, right

let item1 = document.getElementById('item-1');
let item1R = document.getElementById('nav-1R');
let item2 = document.getElementById('item-2');
let item2L = document.getElementById('nav-2L');
let item2R = document.getElementById('nav-2R');
let item3 = document.getElementById('item-3');
let item3L = document.getElementById('nav-3L');

let item10 = document.getElementById('item-10');
let item10R = document.getElementById('nav-10R');
let item11 = document.getElementById('item-11');
let item11L = document.getElementById('nav-11L');
let item11R = document.getElementById('nav-11R');
let item12 = document.getElementById('item-12');
let item12L = document.getElementById('nav-12L');

let item20 = document.getElementById('item-20');
let item20R = document.getElementById('nav-20R');
let item21 = document.getElementById('item-21');
let item21L = document.getElementById('nav-21L');
let item21R = document.getElementById('nav-21R');
let item22 = document.getElementById('item-22');
let item22L = document.getElementById('nav-22L');

item1R.addEventListener('click', () => { navAction('1R') });
item2L.addEventListener('click', () => { navAction('2L') });
item2R.addEventListener('click', () => { navAction('2R') });
item3L.addEventListener('click', () => { navAction('3L') });

item10R.addEventListener('click', () => { navAction('10R') });
item11L.addEventListener('click', () => { navAction('11L') });
item11R.addEventListener('click', () => { navAction('11R') });
item12L.addEventListener('click', () => { navAction('12L') });

item20R.addEventListener('click', () => { navAction('20R') });
item21L.addEventListener('click', () => { navAction('21L') });
item21R.addEventListener('click', () => { navAction('21R') });
item22L.addEventListener('click', () => { navAction('22L') });

function navAction(item) {
    if (item=='1R') {
        item1.style.display='none';
        item2.style.display='inline';
    } else if (item=='2L') {
        item1.style.display='inline';
        item2.style.display='none';
    } else if (item=='2R') {
        item2.style.display='none';
        item3.style.display='inline';
    } else if (item=='3L') {
        item2.style.display='inline';
        item3.style.display='none';
    } else if (item=='10R') {
        item10.style.display='none';
        item11.style.display='inline';
    } else if (item=='11L') {
        item10.style.display='inline';
        item11.style.display='none';
    } else if (item=='11R') {
        item11.style.display='none';
        item12.style.display='inline';
    } else if (item=='12L') {
        item11.style.display='inline';
        item12.style.display='none';
    } else if (item=='20R') {
        item20.style.display='none';
        item21.style.display='inline';
    } else if (item=='21L') {
        item20.style.display='inline';
        item21.style.display='none';
    } else if (item=='21R') {
        item21.style.display='none';
        item22.style.display='inline';
    } else if (item=='22L') {
        item21.style.display='inline';
        item22.style.display='none';
    }
}

//View buttons
let view1 = document.getElementById('view-1');
let view2 = document.getElementById('view-2');
let view4 = document.getElementById('view-4');
let view5 = document.getElementById('view-5');
let view6 = document.getElementById('view-6');

let menuitem1 = document.getElementById('hidden-menu-1');
let menuitem2 = document.getElementById('hidden-menu-2');
let menuitem4 = document.getElementById('hidden-menu-4');
let menuitem5 = document.getElementById('hidden-menu-5');
let menuitem6 = document.getElementById('hidden-menu-6');

view1.addEventListener('click', () => { menuAction('1') });
view2.addEventListener('click', () => { menuAction('2') });
view4.addEventListener('click', () => { menuAction('4') });
view5.addEventListener('click', () => { menuAction('5') });
view6.addEventListener('click', () => { menuAction('6') });

function menuAction(item) {
    if (item=='1') {
        menuitem1.style.display='inline';
        menuitem2.style.display='none';
        menuitem4.style.display='none';
        menuitem5.style.display='none';
        menuitem6.style.display='none';
    } else if (item=='2') {
        menuitem1.style.display='none';
        menuitem2.style.display='inline';
        menuitem4.style.display='none';
        menuitem5.style.display='none';
        menuitem6.style.display='none';
    } else if (item=='4') {
        menuitem1.style.display='none';
        menuitem2.style.display='none';
        menuitem4.style.display='inline';
        menuitem5.style.display='none';
        menuitem6.style.display='none';
    } else if (item=='5') {
        menuitem1.style.display='none';
        menuitem2.style.display='none';
        menuitem4.style.display='none';
        menuitem5.style.display='inline';
        menuitem6.style.display='none';
    } else if (item=='6') {
        menuitem1.style.display='none';
        menuitem2.style.display='none';
        menuitem4.style.display='none';
        menuitem5.style.display='none';
        menuitem6.style.display='inline';
    }
}

document.addEventListener('click', (event) => {
    // Check if the clicked target is not view1 or a child of view1
    if (!view1.contains(event.target) && event.target !== view1) {
        menuitem1.style.display = 'none';
    }

    if (!view2.contains(event.target) && event.target !== view2) {
        menuitem2.style.display = 'none';
    }

    if (!view4.contains(event.target) && event.target !== view4) {
        menuitem4.style.display = 'none';
    }

    if (!view5.contains(event.target) && event.target !== view5) {
        menuitem5.style.display = 'none';
    }

    if (!view6.contains(event.target) && event.target !== view6) {
        menuitem6.style.display = 'none';
    }
});
