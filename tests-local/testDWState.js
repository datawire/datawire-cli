var DatawireState = require('DatawireState').DatawireState.DatawireState;

var dwState = new DatawireState();

console.log("Loading state from " + dwState.defaultStatePath());

dwState.loadDefaultState();

console.log("-- we are [" + dwState.getCurrentOrgID() + "]" + dwState.getCurrentEmail());
console.log("-- animated: " + dwState.getCurrentServiceToken('animated'));
