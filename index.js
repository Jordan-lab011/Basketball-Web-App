import express from "express";
import axios from "axios";
import bodyParser from "body-parser";


const app = express();
const port = 3000;
const NBA_API_URL = "http://localhost:8000"
const google_api_key = "AIzaSyCtM6oJIUAi8dK9HcYm5-AV1KIRAYHh8gw"
const cx = "97288c4fc65664c6f"
// Available stat categories for /leaders endpoint
const statsOptions = {
  "PTS":"Points per game" ,
  "REB":"Rebounds per game" ,
  "AST":"Assists per game" ,
  "STL":"Steals per game" ,
  "BLK":"Blocks per game" ,
  "FG3M":"3-Pointers per game" ,
  "FG3_PCT":"3-Pointers % " ,
  "FGM":"Field goals per game" ,
  "FG_PCT":"Field Goal % " ,
};

// Possible limits
const limits = [5, 10, 20, 50, 100];


app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"))



app.get("/", async(req, res) => { 
  const response = await axios.get(`${NBA_API_URL}/player-of-the-day`); 
  const data = (response.data); 
  console.log(data);
  const player = data.player_of_the_day.Player;
  console.log(player);

  // Fetching player image using Google Custom Search API
  const searchResponse = await axios.get("https://www.googleapis.com/customsearch/v1", {
    params: {
      key: "AIzaSyCtM6oJIUAi8dK9HcYm5-AV1KIRAYHh8gw",
      cx: "97288c4fc65664c6f",
      q: player,
      num: 1,
      dateRestrict: "d[1]",
      imgSize: "xlarge",
      searchType: "image"
    }
  });      
  const searchData = searchResponse.data;
  const playerImage = searchData.items[0].link;
  console.log(playerImage);
  res.render("index.ejs", {
    date: data.date,
    playerOfTheDay: data.player_of_the_day,
    team: data.Team,
    pts: data.Points,
    rebs: data.Rebounds,
    asts: data.Assists,
    opp: data.Opponent,
    imageSrc: playerImage,
  });
});

app.get("/matches-today", async(req, res) => { 
  const response = await axios.get(`${NBA_API_URL}/matches-of-the-day`); 
  const data = (response.data); 
  const games = data.games
  const matchups = []
  console.log(games);
  if (games[0].matchup){
    games.forEach(game => {
      matchups.push(game.matchup)
    });
    console.log(matchups)
    res.render("matches.ejs", {
       matches: matchups
    });
  } else {
    res.render("matches.ejs")
  }
});


app.get("/player-stats", async(req, res) => {
  res.render("player-stats.ejs", {action:"/player-stats"});
});

app.post("/player-stats", async(req, res) => {
  const playerName = req.body.playerName;
  console.log(playerName);

  const response = await axios.get(`${NBA_API_URL}/search-player`, {
    params: { name: playerName }
  });
   const data = response.data;
  console.log(data);
  const player_id = data[0].id

const playerStats = await axios.get(`${NBA_API_URL}/player-stats/${player_id}`);

  const playerImage = await axios.get("https://www.googleapis.com/customsearch/v1", {
    params: {
      key: google_api_key,
      cx: cx,
      q: playerName,
      num: 1,
      dateRestrict: "d[1]",
      imgSize: "xlarge",
      searchType: "image"
    }
  });      
  const imageData = playerImage.data;
  const imageLink = imageData.items[0].link;

 res.render("player-stats.ejs", {
  action:"/player-stats",
  imgSrc: imageLink,
  stats: playerStats,
  playerName: playerName
});
  
});


app.get("/league-leaders", async(req, res) => {
  res.render("league-leaders.ejs",{statsOptions, limits});
});


app.post("/league-leaders", async(req, res) => {
  const statCategory = req.body.stat;
  const limit = parseInt(req.body.limit);
  console.log(statCategory, limit);

  if (!Object.keys(statsOptions).includes(statCategory)) {
    return res.status(400).send("Invalid stat category");
  }

  if (!limits.includes(limit)) {
    return res.status(400).send("Invalid limit");
  }

  const response = await axios.get(`${NBA_API_URL}/leaders`, {
    params: {
      stat: statCategory,
      limit: limit
    }
  });

  const data = response.data;
  console.log(data);

  res.render("league-leaders.ejs", {
    statsOptions,
    limits,
    leaders: data.leaders,
    categoryAbbr: data.stat_category,
    selectedStat: statsOptions[statCategory],
    selectedLimit: limit
  });
})


app.get("/player-comparison", async(req, res) => {
  res.render("player-comparison.ejs", {action:"/player-comparison"});
});
app.post("/player-comparison", async(req, res) => {
  const player1Name = req.body.player1Name;
  const player2Name = req.body.player2Name;

  console.log(player1Name, player2Name);

  const response1 = await axios.get(`${NBA_API_URL}/search-player`, {
    params: { name: player1Name }
  });
  const data1 = response1.data;
  const player1_id = data1[0].id;

  const response2 = await axios.get(`${NBA_API_URL}/search-player`, {
    params: { name: player2Name }
  });
  const data2 = response2.data;
  const player2_id = data2[0].id;

  const playerStats1 = await axios.get(`${NBA_API_URL}/player-stats/${player1_id}`);
  const playerStats2 = await axios.get(`${NBA_API_URL}/player-stats/${player2_id}`);

  res.render("player-comparison.ejs", {
    action: "/player-comparison",
    player1: data1[0],
    player2: data2[0],
    stats1: playerStats1.data,
    stats2: playerStats2.data
  });
});


app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
  });
  