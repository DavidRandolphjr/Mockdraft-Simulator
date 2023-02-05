document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#startbutton').addEventListener('click', start);

    
    load_homepage();
});

let url = `ws://${window.location.host}/ws/socket-server/`
const draftSocket = new WebSocket(url)
function load_homepage() {
    
    const view = document.querySelector('#listedplayers')
    const teamrosters = document.querySelector('#TeamRosters')
    
    draftSocket.onmessage = function(e){
        let data = JSON.parse(e.data)
        console.log('Data:', data)
        

        if(data.type === document.getElementById("roomid").innerHTML){
            console.log("this is the url",document.URL)
            console.log('turn','started',data.turn,data.started)
            document.getElementById('countdown').style.display ="none"
            document.getElementById('listedplayers').innerHTML ="";
            
            
            
            if(data.started == true){
                document.getElementById("startbutton").style.display ="none"
                document.getElementById('countdown').style.display ="block"
                
                // retrieve the time left on timer
                fetch('/timer/'+document.getElementById("roomid").innerHTML)
                .then(response => response.json())
                .then(timer => {
                    console.log("this is the timer",timer)
                    var timeleft = 60 - timer;
                    var downloadTimer = setInterval(function(){
                    if(timeleft <= 0 && document.getElementById('user-name').value == data.turn){
                        
                        timeleft=0
                        clearInterval(downloadTimer);
                        draftSocket.send(JSON.stringify({
                            'message':"unimportant",
                            'roomid':document.getElementById('roomid').innerHTML,
                            'username':document.getElementById('user-name').value,
                            'command':"autodraft"
                        }))
                        
                    }

                    // clear timer if time is 0 and its user's turn
                    if(timeleft <= 0 && document.getElementById('user-name').value != data.turn){
                        
                        clearInterval(downloadTimer);
                          
                    }
                    // check every two seconds to see if the time has been reset
                    if(timeleft % 2 == 0){
                        fetch('/timer/'+document.getElementById("roomid").innerHTML)
                        .then(response => response.json())
                        .then(timer1 => {
                            if(timeleft + timer1 < 59){
                                clearInterval(downloadTimer)
                            }
                        })
                    }
                    
                    document.getElementById("countdown").innerHTML = timeleft;
                    timeleft -= 1;
                    
                    }, 1000); 

                    // grabs player list and allows user to draft
                    fetch(`/player_list?roomid=${document.getElementById('roomid').innerHTML}`)
                    .then(response => response.json())
                    .then(players => {
                        players.forEach(player =>{
                            // if its the user's turn, allow them to draft
                            if(document.getElementById('user-name').value == data.turn){
                                let div = document.createElement('div')
                                div.innerHTML=`
                                <div class = "row" style="border-bottom: 2px solid;">
                                    <div class = "col col-3">
                                        <p>${player['playername']}</p>
                                    </div>
                                    <div class = "col col-1">
                                        <p>${player['pos']}</p>
                                    </div>
                                    <div class = "col col-4">
                                        <button class="btn btn-primary" id="draft${player['playername']}" >Draft</button>
                                    </div>
                                </div>
                                `
                                view.append(div)

                                // add event listner for the draft button to send info back to consumers.py
                                let form = document.getElementById('draft' + player['playername'])
                                form.addEventListener('click', (e)=> {
                                    
                                    clearInterval(downloadTimer);
                                    e.preventDefault()
                                    const message = [player['playername'], player['pos'] ]
                                    draftSocket.send(JSON.stringify({
                                        'message':message,
                                        'roomid':document.getElementById('roomid').innerHTML,
                                        'username':document.getElementById('user-name').value,
                                        'command':"draft"
                                    }))
                            
                                }) 

                            }
                            else{
                                let div = document.createElement('div')
                                div.innerHTML=`
                                <div class = "row" style="border-bottom: 2px solid;">
                                    <div class = "col col-3">
                                        <p>${player['playername']}</p>
                                    </div>
                                    <div class = "col col-1">
                                        <p>${player['pos']}</p>
                                    </div>
                                </div>
                                `
                                view.append(div)
                            }
                        })
                        
                    })
                    
                })    
                
            }
            var counter = 1

            // this fetch request gets the team information for who owns which team.
            fetch('/teamsinfo/'+document.getElementById("roomid").innerHTML)
            .then(response => response.json())
            .then(rosters => {
                teamrosters.innerHTML=""
                const owners_list = []
                rosters.forEach(roster=>{owners_list.push(roster['owner'])})
                rosters.forEach(roster=>{
                    let teamownerdiv = document.createElement('div')
                    teamownerdiv.id = 'column'+counter
                    if(roster['owner'] == "AI"){
                        teamownerdiv.innerHTML=`
                        
                            <div id="team"${counter}>Team Roster ${counter}</div>
                            <span id="division${counter}" ></span>
                            <span id="claim${roster['id']}" hidden>${counter}</span>
                            
                        `
                        teamrosters.append(teamownerdiv)
                    }
                    else{
                        teamownerdiv.innerHTML=`
                        
                            <div id="team"${counter}>${roster['owner']}'s Team</div>
                            <span id="division${counter}" ></span>
                            <span id="claim${roster['id']}" hidden>${counter}</span>
                            
                        `
                        teamrosters.append(teamownerdiv)
                    }
                    
                    // create a button to claim a team
                    claimButton = document.createElement('button')
                    claimButton.className = "btn btn-primary"
                    claimButton.innerHTML="Claim"
                    claimButton.addEventListener('click', function(){
                        const message = [document.getElementById("claim"+roster['id']).innerHTML, document.URL]
                        draftSocket.send(JSON.stringify({
                            'message':message,
                            'roomid':document.getElementById('roomid').innerHTML,
                            'username':document.getElementById('user-name').value,
                            'command':"claim"
                        }))
                        
                        
                    })
                    if(document.getElementById('user-name').value == roster['owner']){
                        document.getElementById('column'+counter).style.backgroundColor = 'LightGreen'  
                    }
                    else{
                        document.getElementById('column'+counter).style.backgroundColor = 'white'
                    }
                    //this is where we add the button
                    
                    if (roster['owner'] == "AI"){
                        document.getElementById("division"+counter).appendChild(claimButton)
                    }
                    if (owners_list.includes(document.getElementById('user-name').value)){
                        document.getElementById("division"+counter).innerHTML= ""
                    }
                    counter +=1
                    
                })
            })
            //Show the player that was drafted
            fetch('/teamrosters/'+document.getElementById("roomid").innerHTML)
            .then(response => response.json())
            .then(teamrosters =>{
                var ros_count = 1
                teamrosters.forEach(teamroster=>{
                    console.log("testing",teamroster['roster'],teamroster['pos'])
                    let i = 1;
                    while(i< teamroster['roster'].length+1){
                        document.getElementById("roster"+ros_count+"i"+i).innerHTML = teamroster['roster'][i-1]
                        document.getElementById("roster"+ros_count+"i"+i).className= teamroster['pos'][i-1]
                        i++;
                    }
                    ros_count++;
                })

            })
        }

        // if the user connects for the first time, this if statement will controll what the user sees
        if(data.type === 'firstload'){
            teamrosters.innerHTML=""
            var counter = 1

            // this fetch request gets the team information for who owns which team.
            fetch('/teamsinfo/'+document.getElementById("roomid").innerHTML)
            .then(response => response.json())
            .then(rosters => {
                teamrosters.innerHTML=""
                const owners_list = []
                rosters.forEach(roster=>{owners_list.push(roster['owner'])})
                console.log("is this even working")
                rosters.forEach(roster=>{
                    
                    let teamownerdiv = document.createElement('div')
                    teamownerdiv.id = 'column'+counter
                    if(roster['owner'] == "AI"){
                        teamownerdiv.innerHTML=`
                        
                            <div id="team"${counter}>Team Roster ${counter}</div>
                            <span id="division${counter}" ></span>
                            <span id="claim${roster['id']}" hidden>${counter}</span>
                            
                        `
                        teamrosters.append(teamownerdiv)
                    }
                    else{
                        teamownerdiv.innerHTML=`
                        
                            <div id="team"${counter}>${roster['owner']}'s Team</div>
                            <span id="division${counter}" ></span>
                            <span id="claim${roster['id']}" hidden>${counter}</span>
                            
                        `
                        teamrosters.append(teamownerdiv)
                    }
                    // create button to claim teams
                    claimButton = document.createElement('button')
                    claimButton.className = "btn btn-primary"
                    claimButton.innerHTML="Claim"
                    // claim teams by adding an event listener to send info back to consumers.py
                    claimButton.addEventListener('click', function(){
                        const message = [document.getElementById("claim"+roster['id']).innerHTML, document.URL]
                        draftSocket.send(JSON.stringify({
                            'message':message,
                            'roomid':document.getElementById('roomid').innerHTML,
                            'username':document.getElementById('user-name').value,
                            'command':"claim"
                        }))
                        
                        
                    })
                    // add background color to the user's team
                    if(document.getElementById('user-name').value == roster['owner']){
                        document.getElementById('column'+counter).style.backgroundColor = 'LightGreen' 
                    }
                    else{
                        document.getElementById('column'+counter).style.backgroundColor = 'white'
                    }

                    
                    if (roster['owner'] == "AI"){
                        document.getElementById("division"+counter).appendChild(claimButton)
                    }
                    if (owners_list.includes(document.getElementById('user-name').value)){
                        document.getElementById("division"+counter).innerHTML= ""
                    }
                    counter +=1
                    
                })
            })

            // this fill sthe page with the players that the teams drafted.
            fetch('/teamsinfo/'+document.getElementById("roomid").innerHTML)
            .then(response => response.json())
            .then(teamrosters =>{
                var ros_count = 1
                teamrosters.forEach(teamroster=>{
                    console.log("testing",teamroster['roster'])
                    let i = 1;
                    while(i< teamroster['roster'].length+1){
                        document.getElementById("roster"+ros_count+"i"+i).innerHTML = teamroster['roster'][i-1]
                        i++;
                    }
                    ros_count++;
                })

            })

            // prompts the user to rejoin if the draft has already started and the user disconnected and reconnected
            if(document.getElementById("startbutton").value == "True"){
                let confirmAction = confirm("You will be rejoining");
                if (confirmAction) {
                    draftSocket.send(JSON.stringify({
                        'message':"howdy",
                        'roomid':document.getElementById('roomid').innerHTML,
                        'username':document.getElementById('user-name').value,
                        'command':"rejoin"
                    }));
                } else {
                alert("Action canceled");
                }
            }
        }
    }    
}
// function to start the draft
function start(e){
    e.preventDefault();
    draftSocket.send(JSON.stringify({
        'message':"hello fren",
        'roomid':document.getElementById('roomid').innerHTML,
        'username':document.getElementById('user-name').value,
        'command':"start"
    }))
}