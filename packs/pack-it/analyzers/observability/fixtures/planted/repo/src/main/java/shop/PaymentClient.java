package shop;

import java.io.IOException;

class PaymentClient {
    void send(Gateway g) {
        try {
            g.post();
        } catch (Exception e) {}
    }
}
