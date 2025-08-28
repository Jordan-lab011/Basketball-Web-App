import express from "express";
import axios from "axios";
import bodyParser from "body-parser";
import dotenv from "dotenv";

dotenv.config();


const app = express();
const port = 3000;
const remove_bg_api_key = "kosGSCqVN7xuNSGhc3i4yR15"
const NBA_API_URL = "http://localhost:8000"
const google_api_key = "AIzaSyCtM6oJIUAi8dK9HcYm5-AV1KIRAYHh8gw"
const cx = "97288c4fc65664c6f"
const imgSize = "xlarge";
const playerImageAction =" png"
const daysAgo = 1; // Restrict to images from the last day
const dateRestrict = `d[${daysAgo}]`; // Restrict to images from the last day
const imgColorType = "trans"

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
// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"))


// FUNCTIONS
function getStats(data, playerData) {
  const perGame = playerData.GP;
  const playerStats = {
    name: data.fullName,
    team: data.currentTeam,
    stats: {
      PTS: (playerData.PTS / perGame).toFixed(1),
      REB: (playerData.REB / perGame).toFixed(1),
      AST: (playerData.AST / perGame).toFixed(1),
      STL: (playerData.STL / perGame).toFixed(1),
      BLK: (playerData.BLK / perGame).toFixed(1),
      FG3M: (playerData.FG3M / perGame).toFixed(1),
      FG3_PCT: (playerData.FG3_PCT * 100).toFixed(1) + "%",
      FGM: (playerData.FGM / perGame).toFixed(1),
      FG_PCT: (playerData.FG_PCT*100).toFixed(1) + "%",
    }
  }
  return playerStats;
}

async function getImageUrl(playerName) {
  try {
    const response = await axios.get("https://www.googleapis.com/customsearch/v1", {
      params: {
        key: google_api_key,
        cx: cx,
        q: playerName + playerImageAction,
        num: 1,
        dateRestrict: dateRestrict,
        imgSize: imgSize,
        searchType: "image",
        imgColorType: imgColorType,
      }
    });
    const searchData = response.data;
    return searchData.items[0].link; // Return the first image link
  } catch (error) {
    console.error("Error fetching image:", error);
    return null; // Return null if there's an error
  }
}

async function getPlayerData(playerName) {
  try {
    const response = await axios.get(`${NBA_API_URL}/search-player`, {
      params: { name: playerName }
    });
    const data = response.data;
    if (data.length > 0) {
      const playerData = {
        id: data[0].id,
        fullName: data[0].full_name,
        currentTeam: data[0].current_team,
      }
      return playerData; // Returns the player's data
    } else {
      throw new Error("Player not found");
    }
  } catch (error) {
    console.error("Error fetching player ID:", error);
    throw error; // Rethrow the error for handling in the route
  }
}

function getFinalScore(game){
  const teams = game.matchup.split(" vs ");
  const team1 = teams[0]
  const team2 = teams[1]
  var team1Score = 0;
  var team2Score = 0;
  game.players.forEach(player => {
    if (!player.pts) {
      return; // Skip players without points
    }
    if (player.team === team1) {
      team1Score += player.pts;
    } else if (player.team === team2) {
      team2Score += player.pts;
    }
  });
  if ( team1Score > team2Score) {
    var team1Status = "W";
    var team2Status = "L";
  } else{
    var team1Status = "L";
    var team2Status = "W";
  }
  return{
    team1: team1,
    team2: team2,
    team1Score: team1Score,
    team2Score: team2Score,
    team1Status: team1Status,
    team2Status: team2Status
  }
}


app.get("/", async(req, res) => { 
  try {
    const response = await axios.get(`${NBA_API_URL}/player-of-the-day`);
    const data = (response.data); 
  console.log(data);
  if (!data.player_of_the_day){
    res.render("index.ejs", {
      message: data.message
    });
    return;
  }
  const player = data.player_of_the_day.Player;
  console.log(player);

  // Fetching player image using Google Custom Search API
  const playerImage = await getImageUrl(player);
  const stats = data.player_of_the_day;

  res.render("index.ejs", {
    date: stats.date,
    playerOfTheDay: stats.Player,
    team: stats.Team,
    PTS: stats.Points,
    REB: stats.Rebounds,
    AST: stats.Assists,
    opp: stats.Opponent,
    imageSrc: playerImage,
  });

  } catch (e) {
    res.render("index.ejs", {
      message:"NBA stats API is unavailable at the moment",
  })
  }
  
});

app.get("/matches-today", async(req, res) => { 
  const response = await axios.get(`${NBA_API_URL}/matches-of-the-day`); 
  const data = (response.data); 
  const games = data.games
  const matchups = [];

  if (games[0]){
    games.forEach(game => {
      if (game.players){
        if (game.time.toLowerCase().includes("final")){ // Completed matches
          const matchup = {
            matchup: game.matchup,
            status: "Final",
            statusCode: "red",
            finalScore: getFinalScore(game),
            boxscore: game.players
          };
          matchups.push(matchup)
        }else{// Live matches
          const matchup = {
            matchup: game.matchup,
            status: "Live",
            statusCode: "yellow",
            finalScore: getFinalScore(game),
            boxscore: game.players
          };
          matchups.push(matchup)
        }
      } else {// Matches not started
        const matchup = {
            matchup: null,
            status: game.time,
            statusCode: "grey",
            finalScore: null,
            boxscore: null
          };
        matchups.push(matchup)
      };
    });
    console.log(matchups)
    
    res.render( "matches.ejs", {
      matches: matchups
    });
  } else {
    res.render("matches.ejs", {
      message: games.message
    });
  }
});


app.get("/player-stats", async(req, res) => {
  res.render("player-stats.ejs", {action:"/player-stats"});
});

app.post("/player-stats", async(req, res) => {
  const playerName = req.body.playerName;
  console.log(playerName);

  const playerData = await getPlayerData(playerName);
  const playerId = playerData.id;
  const playerStats = await axios.get(`${NBA_API_URL}/player-stats/${playerId}`);
  console.log(playerStats.data);

  const imageLink = await getImageUrl(playerName);
  console.log(imageLink);

  const raw_stats = playerStats.data.stats
  const stats = getStats(playerData, raw_stats); 

 res.render("player-stats.ejs", {
  action:"/player-stats",
  imgSrc: imageLink,
  stats: stats.stats,
  playerName: playerName,
  team:stats.team,
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
  const player1Name = req.body.player1;
  const player2Name = req.body.player2;
  console.log(player1Name, player2Name);

  const player1Data = await getPlayerData(player1Name);
  const player1_id = player1Data.id;
  const player2Data= await getPlayerData(player2Name);
  const player2_id = player2Data.id;

  const playerStats1 = await axios.get(`${NBA_API_URL}/player-stats/${player1_id}`);
  const playerStats2 = await axios.get(`${NBA_API_URL}/player-stats/${player2_id}`);

  const player1AllStats = playerStats1.data.stats;
  const player2AllStats = playerStats2.data.stats;
  
  const player1Stats = getStats(player1Data, player1AllStats);
  const player2Stats = getStats(player2Data, player2AllStats);
  console.log(player1Stats, player2Stats);

  res.render("player-comparison.ejs", {
    action: "/player-comparison",
    player1Stats,
    player2Stats,
  });
});


app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
  });
  