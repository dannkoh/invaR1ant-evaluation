public class SimpleAscendingLast {

    private static boolean worstCase = false;

    public static void algo(int[] a) {
        boolean fail = false;
        boolean skip = false;
        final int N = a.length;
        for (int i = 0; i < N; i++) {
            if (N != 1 & i == N-2) {
                if (a[N-1] < a[0]){
                    // Skip
                    skip = true;
                } else {
                    fail = true;
                }
            } else {
                if (a[i] < a[i+1]){
                    // Skip
                    skip = true;
                } else {
                    fail = true;
                }
            }
        }
        if (!fail) {
            worstCase = true;
            int aa = 99999;
            for (int i = 0; i < N; i++) {
                aa = aa*aa;
            }
        }
        System.out.println(worstCase);
    }

    public static void main(String[] args) {
        final int N = args.length;
        int[] a = new int[N];
        for (int i = 0; i < N; i++) {
            a[i] = Integer.parseInt(args[i]);
        }
        // We only measure the complexity of this function itself.
        algo(a);
    }
}
