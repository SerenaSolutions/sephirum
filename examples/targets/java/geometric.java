// Gerado pelo TRANSPILER MULTI-ALVO ZEPHIRUM (autônomo).
// Familia: geometric_inf - pergunta: < 2 - §EXACT long; §12: ±9,2e18
import java.security.MessageDigest;

public class ZephOut {{
    static int cmp128(long a, long b) {{
        // produtos cruzados no intervalo long desta fatia (§12)
        return Long.compare(a, b);
    }}
    public static void main(String[] args) throws Exception {{
        String DATA = "1|1/2";
        String OP = "<";
        long THR = 2L, UNITS = 2L;
        long A=1L,B=1L,P=1L,Q=2L; // |r|<1 garantido
int c = cmp128(A*Q, THR*B*(Q-P));
        boolean verdict = (OP.equals(">") && c > 0) || (OP.equals("<") && c < 0)
            || (OP.equals(">=") && c >= 0) || (OP.equals("<=") && c <= 0)
            || (OP.equals("==") && c == 0);
        byte[] h = MessageDigest.getInstance("SHA-256").digest(DATA.getBytes());
        StringBuilder hex = new StringBuilder();
        for (byte b : h) hex.append(String.format("%02x", b));
        System.out.println("VERDICT " + (verdict ? 1 : 0));
        System.out.println("HASH " + hex);
        System.out.println("UNITS " + UNITS);
    }}
}}
