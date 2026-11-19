import { Component } from "@angular/core";

@Component({
  selector: "app-favorite-button",
  template: `
    <button class="btn btn-sm" (click)="toggle()">
      <i class="ion-heart"></i> <ng-content></ng-content>
    </button>
  `,
})
export class FavoriteButtonComponent {
  toggle() {}
}
