package clinic;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class Patient {
    @Id
    private Long id;
    private String lastName;
    private String ward;
}
