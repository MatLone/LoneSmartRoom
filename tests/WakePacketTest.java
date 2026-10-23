import com.lonesmartroom.app.WakeOnLan;
import java.util.Arrays;

// Executes the compiled production packet builder, never a valid UDP send.
class WakePacketTest {
    static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    static void rejects(Runnable operation) {
        try { operation.run(); }
        catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("Expected validation rejection before socket creation");
    }
    public static void main(String[] args) {
        byte[] packet = WakeOnLan.INSTANCE.magicPacket("02:AB:CD:10:20:30");
        require(packet.length == 102, "Magic packet must be 102 bytes");
        for (int i = 0; i < 6; i++) require(packet[i] == (byte) 0xff, "Missing FF header");
        byte[] destination = {2, (byte) 0xab, (byte) 0xcd, 16, 32, 48};
        for (int offset = 6; offset < packet.length; offset += 6)
            require(Arrays.equals(Arrays.copyOfRange(packet, offset, offset + 6), destination),
                    "Destination MAC repetition mismatch");
        require(Arrays.equals(packet, WakeOnLan.INSTANCE.magicPacket("02-ab-cd-10-20-30")),
                "MAC normalization changed");
        rejects(() -> WakeOnLan.INSTANCE.magicPacket("invalid"));
        rejects(() -> WakeOnLan.INSTANCE.send("02:AB:CD:10:20:30", "255.255.255.255", 80));
        rejects(() -> WakeOnLan.INSTANCE.send("02:AB:CD:10:20:30", "999.1.1.1", 9));
        rejects(() -> WakeOnLan.INSTANCE.send("02:AB:CD:10:20:30", "host.example", 9));
        System.out.println("PASS: production WoL packet, MAC normalization and invalid-input guards; no UDP sent.");
    }
}
