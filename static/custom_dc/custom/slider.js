let item1 = document.getElementById("item-1");
let item1R = document.getElementById("nav-1R");
let item2 = document.getElementById("item-2");
let item2L = document.getElementById("nav-2L");
let item2R = document.getElementById("nav-2R");
let item3 = document.getElementById("item-3");
let item3L = document.getElementById("nav-3L");
let item3R = document.getElementById("nav-3R");
let item4 = document.getElementById("item-4");
let item4L = document.getElementById("nav-4L");

let item10 = document.getElementById("item-10");
let item10R = document.getElementById("nav-10R");
let item11 = document.getElementById("item-11");
let item11L = document.getElementById("nav-11L");
let item11R = document.getElementById("nav-11R");
let item12 = document.getElementById("item-12");
let item12L = document.getElementById("nav-12L");

let item20 = document.getElementById("item-20");
let item20R = document.getElementById("nav-20R");
let item21 = document.getElementById("item-21");
let item21L = document.getElementById("nav-21L");
let item21R = document.getElementById("nav-21R");
let item22 = document.getElementById("item-22");
let item22L = document.getElementById("nav-22L");

item1R.addEventListener("click", () => {
  navAction("1R");
});
item2L.addEventListener("click", () => {
  navAction("2L");
});
item2R.addEventListener("click", () => {
  navAction("2R");
});
item3L.addEventListener("click", () => {
  navAction("3L");
});
item3R.addEventListener("click", () => {
  navAction("3R");
});
item4L.addEventListener("click", () => {
  navAction("4L");
});

item10R.addEventListener("click", () => {
  navAction("10R");
});
item11L.addEventListener("click", () => {
  navAction("11L");
});
item11R.addEventListener("click", () => {
  navAction("11R");
});
item12L.addEventListener("click", () => {
  navAction("12L");
});

item20R.addEventListener("click", () => {
  navAction("20R");
});
item21L.addEventListener("click", () => {
  navAction("21L");
});
item21R.addEventListener("click", () => {
  navAction("21R");
});
item22L.addEventListener("click", () => {
  navAction("22L");
});

function navAction(item) {
  if (item == "1R") {
    item1.style.display = "none";
    item2.style.display = "inline";
  } else if (item == "2L") {
    item1.style.display = "inline";
    item2.style.display = "none";
  } else if (item == "2R") {
    item2.style.display = "none";
    item3.style.display = "inline";
  } else if (item == "3L") {
    item2.style.display = "inline";
    item3.style.display = "none";
  } else if (item == "3R") {
    item3.style.display = "none";
    item4.style.display = "inline";
  } else if (item == "4L") {
    item3.style.display = "inline";
    item4.style.display = "none";
  } else if (item == "10R") {
    item10.style.display = "none";
    item11.style.display = "inline";
  } else if (item == "11L") {
    item10.style.display = "inline";
    item11.style.display = "none";
  } else if (item == "11R") {
    item11.style.display = "none";
    item12.style.display = "inline";
  } else if (item == "12L") {
    item11.style.display = "inline";
    item12.style.display = "none";
  } else if (item == "20R") {
    item20.style.display = "none";
    item21.style.display = "inline";
  } else if (item == "21L") {
    item20.style.display = "inline";
    item21.style.display = "none";
  } else if (item == "21R") {
    item21.style.display = "none";
    item22.style.display = "inline";
  } else if (item == "22L") {
    item21.style.display = "inline";
    item22.style.display = "none";
  }
}
