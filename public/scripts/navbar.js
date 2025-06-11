const sidebar = document.querySelector(".sidebar");
const menu = document.querySelector("#menu");

const main = document.querySelector(".main");

const menu_container = document.querySelector(".menu-container");
const logout_container = document.querySelector(".logout-container");

const icon_logout = document.querySelector(".icon-logout");

const playerOfTheDay = document.querySelector("#playerOfTheDay");
const matches = document.querySelector("#matches");
const playerStats = document.querySelector("#playerStats");
const playerComparison = document.querySelector("#playerComparison");
const leagueLeaders = document.querySelector("#leagueLeaders");
const safe2hoop = document.querySelector("#safe2hoop");

let previousToggled = null;
let currentToggled = null;

playerOfTheDay.addEventListener("click", (e) => {
  toggleMenu(playerOfTheDay);
});

matches.addEventListener("click", (e) => {
  toggleMenu(matches);
});

playerStats.addEventListener("click", (e) => {
  toggleMenu(playerStats);
});

playerComparison.addEventListener("click", (e) => {
  toggleMenu(playerComparison);
});

leagueLeaders.addEventListener("click", (e) => {
  toggleMenu(leagueLeaders);
});

safe2hoop.addEventListener("click", (e) => {
  toggleMenu(safe2hoop);
});

const toggleMenu = (button) => {
  if (previousToggled && button !== menu) {
    untoggleMenu(previousToggled);
  }

  button.classList.add("toggled");
  button.style.backgroundColor = "#C9082A";

  if (button !== menu) {
    previousToggled = button;
  }
};

const untoggleMenu = (button) => {
  button.classList.remove("toggled");
  button.style.backgroundColor = "#18c29c";
};

menu.addEventListener("click", (e) => {
  sidebar.classList.contains("active") ? closeMenu() : openMenu();
});

const openMenu = () => {
  sidebar.classList.add("active");
  sidebar.style.width = "250px";

  toggleMenu(menu);

  let menu_logo = document.createElement("img");
  menu_logo.id = "menu-logo";
  menu_logo.src = "/assets/images/logo.svg";
  menu_logo.style.width = "60px";
  menu_container.style.paddingLeft = "15px";
  menu_container.insertBefore(menu_logo, menu_container.childNodes[0]);

  let p_playerOfTheDay = document.createElement("p");
  p_playerOfTheDay.id = "p-playerOfTheDay";
  p_playerOfTheDay.innerHTML = "Player Of The Day";
  playerOfTheDay.style.width = "220px";
  playerOfTheDay.style.justifyContent = "left";
  playerOfTheDay.appendChild(p_playerOfTheDay);

  let p_dash = document.createElement("p");
  p_dash.id = "p-matches";
  p_dash.innerHTML = "Matches Today";
  matches.style.width = "220px";
  matches.style.justifyContent = "left";
  matches.appendChild(p_dash);

  let p_playerStats = document.createElement("p");
  p_playerStats.id = "p-playerStats";
  p_playerStats.innerHTML = "Player Stats";
  playerStats.style.width = "220px";
  playerStats.style.justifyContent = "left";
  playerStats.appendChild(p_playerStats);

  let p_playerComparison = document.createElement("p");
  p_playerComparison.id = "p-playerComparison";
  p_playerComparison.innerHTML = "Player Comparison";
  playerComparison.style.width = "220px";
  playerComparison.style.justifyContent = "left";
  playerComparison.appendChild(p_playerComparison);

  let p_leagueLeaders = document.createElement("p");
  p_leagueLeaders.id = "p-leagueLeaders";
  p_leagueLeaders.innerHTML = "League Leaders";
  leagueLeaders.style.width = "220px";
  leagueLeaders.style.justifyContent = "left";
  leagueLeaders.appendChild(p_leagueLeaders);

  let p_safe2hoop = document.createElement("p");
  p_safe2hoop.id = "p-safe2hoop";
  p_safe2hoop.innerHTML = "Safe to hoop?";
  safe2hoop.style.width = "220px";
  safe2hoop.style.justifyContent = "left";
  safe2hoop.appendChild(p_safe2hoop);

  icon_logout.style.width = "25%";

  let user_container = document.createElement("div");
  user_container.id = "user-container";

  let user_name = document.createElement("p");
  user_name.id = "user-name";
  user_name.innerHTML = "Diego Ferreira";

  let user_role = document.createElement("p");
  user_role.id = "user-role";
  user_role.innerHTML = "Veterinarian";

  user_container.appendChild(user_name);
  user_container.appendChild(user_role);

  logout_container.insertBefore(user_container, logout_container.childNodes[0]);

  let logout_photo = document.createElement("img");
  logout_photo.id = "logout-photo";
  logout_photo.src = "https://github.com/diegoafv.png";
  logout_container.style.paddingLeft = "15px";
  logout_container.insertBefore(logout_photo, logout_container.childNodes[0]);

  main.style.width = "calc(100% - 250px)";
};

const closeMenu = () => {
  menu_container.removeChild(document.getElementById("menu-logo"));
  menu_container.style.paddingLeft = "0px";

  untoggleMenu(menu);

  playerOfTheDay.removeChild(document.getElementById("p-playerOfTheDay"));
  playerOfTheDay.style.width = "50px";
  playerOfTheDay.style.justifyContent = "center";

  matches.removeChild(document.getElementById("p-matches"));
  matches.style.width = "50px";
  matches.style.justifyContent = "center";

  playerStats.removeChild(document.getElementById("p-playerStats"));
  playerStats.style.width = "50px";
  playerStats.style.justifyContent = "center";

  playerComparison.removeChild(document.getElementById("p-playerComparison"));
  playerComparison.style.width = "50px";
  playerComparison.style.justifyContent = "center";

  leagueLeaders.removeChild(document.getElementById("p-leagueLeaders"));
  leagueLeaders.style.width = "50px";
  leagueLeaders.style.justifyContent = "center";

  safe2hoop.removeChild(document.getElementById("p-safe2hoop"));
  safe2hoop.style.width = "50px";
  safe2hoop.style.justifyContent = "center";

  logout_container.removeChild(document.getElementById("logout-photo"));
  logout_container.removeChild(document.getElementById("user-container"));
  logout_container.style.paddingLeft = "0px";

  icon_logout.style.width = "100%";

  sidebar.classList.remove("active");
  sidebar.style.width = "78px";

  main.style.width = "calc(100% - 78px)";
};