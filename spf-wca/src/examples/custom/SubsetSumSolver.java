/**
 * @author Daniel Koh <daniel.koh@student.manchester.ac.uk>
 */

package custom;

import gov.nasa.jpf.symbc.Debug;

public class SubsetSumSolver {

    /**
     * Recursively determines if there is a subset of arr (starting at index)
     * that sums to the target.
     */
    public static boolean subsetSum(int[] arr, int index, int target) {
        if (target == 0) {
            return true;
        }
        if (index >= arr.length) {
            return false;
        }
        // Explore the branch that excludes arr[index] and the branch that includes it.
        return subsetSum(arr, index + 1, target) ||
               subsetSum(arr, index + 1, target - arr[index]);
    }

    public static void main(String[] args) {
        // Parse the desired array size from the command line.
        final int N = Integer.parseInt(args[0]);
        int[] arr = new int[N];
        for (int i = 0; i < N; i++) {
            arr[i] = Debug.makeSymbolicInteger("in" + i);
        }

        // Create a symbolic target.
        int target = Debug.makeSymbolicInteger("target");

        subsetSum(arr, 0, target);
    }
}
