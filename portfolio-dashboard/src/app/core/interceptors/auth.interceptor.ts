import { HttpHandlerFn, HttpRequest } from '@angular/common/http';

export function authInterceptor<T>(req: HttpRequest<T>, next: HttpHandlerFn) {
  // Get the JWT token from localStorage
  const token = localStorage.getItem('jwt_token');

  // If token exists, clone the request and add the Authorization header
  if (token) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  // Pass the request to the next handler
  return next(req);
}
