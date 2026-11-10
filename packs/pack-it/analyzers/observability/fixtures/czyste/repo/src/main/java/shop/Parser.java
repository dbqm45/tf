package shop;

class Parser {
    Integer parse(String s) {
        try {
            return Integer.valueOf(s);
        } catch (NumberFormatException e) {}
        return null;
    }
}
