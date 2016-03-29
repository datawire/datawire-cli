package DWSTester;

import DatawireState.DatawireState;

public class Tester {
    public static void main(String [] args) {
        DatawireState dwState = new DatawireState();

        System.out.println("Loading state from " + dwState.defaultStatePath());

        dwState.loadDefaultState();

        System.out.println("-- we are [" + dwState.getCurrentOrgID() + "]" + dwState.getCurrentEmail());
        System.out.println("-- animated: " + dwState.getCurrentServiceToken("animated"));
    }
}